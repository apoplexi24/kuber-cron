# Troubleshooting Guide

This guide helps you diagnose and fix common issues with Kuber-Cron.

## Common Issues

### 1. Pod Crashes

#### Symptoms
- Pod status shows `CrashLoopBackOff`
- Pod restarts frequently
- Logs show Python errors

#### Diagnosis
```bash
# Check pod status
kubectl get pods -l app=kuber-cron

# Check pod logs
kubectl logs deployment/kuber-cron

# Check previous pod logs
kubectl logs deployment/kuber-cron --previous
```

#### Common Causes and Solutions

1. **Missing Dependencies**
   ```bash
   # Error: ModuleNotFoundError: No module named 'some_module'
   
   # Solution: Add the module to pyproject.toml
   poetry add some_module
   
   # Rebuild and redeploy
   docker build -t kuber-cron:latest .
   kind load docker-image kuber-cron:latest
   kubectl rollout restart deployment/kuber-cron
   ```

2. **Invalid Crontab Syntax**
   ```bash
   # Check crontab configuration
   kubectl get configmap kuber-cron-config -o yaml
   
   # Validate crontab syntax
   kubectl exec deployment/kuber-cron -- crontab -l
   ```

3. **Resource Limits**
   ```bash
   # Check resource usage
   kubectl top pod -l app=kuber-cron
   
   # Adjust limits in deployment.yaml
   resources:
     limits:
       cpu: "1000m"    # Increase CPU limit
       memory: "1Gi"   # Increase memory limit
   ```

### 2. Jobs Not Running

#### Symptoms
- No job output in logs
- Prometheus metrics not updating
- No errors in pod logs

#### Diagnosis
```bash
# Check if crontab is loaded
kubectl exec deployment/kuber-cron -- cat /etc/crontab

# Check job logs
kubectl exec deployment/kuber-cron -- ls -l /var/log/kuber-cron/
kubectl exec deployment/kuber-cron -- cat /var/log/kuber-cron/job.log

# Check metrics
kubectl port-forward deployment/kuber-cron 8000:8000
curl localhost:8000/metrics
```

#### Common Causes and Solutions

1. **Wrong File Permissions**
   ```bash
   # Check file permissions
   kubectl exec deployment/kuber-cron -- ls -l src/jobs/
   
   # Fix permissions
   kubectl exec deployment/kuber-cron -- chmod +x src/jobs/your_job.py
   ```

2. **Incorrect Path**
   ```bash
   # Verify file exists
   kubectl exec deployment/kuber-cron -- ls -l src/jobs/your_job.py
   
   # Update crontab with correct path
   * * * * * python /app/src/jobs/your_job.py
   ```

3. **Timezone Issues**
   ```bash
   # Check container timezone
   kubectl exec deployment/kuber-cron -- date
   
   # Add timezone environment variable
   env:
   - name: TZ
     value: "UTC"
   ```

### 3. Monitoring Issues

#### Symptoms
- Can't access metrics endpoint
- Prometheus metrics not updating
- Connection refused errors

#### Diagnosis
```bash
# Check if metrics server is running
kubectl exec deployment/kuber-cron -- netstat -tlnp

# Test metrics endpoint
kubectl port-forward deployment/kuber-cron 8000:8000
curl localhost:8000/metrics

# Check pod logs for metrics errors
kubectl logs deployment/kuber-cron | grep metrics
```

#### Common Causes and Solutions

1. **Port Not Exposed**
   ```yaml
   # Add ports to deployment.yaml
   ports:
   - containerPort: 8000
     name: metrics
   ```

2. **Network Policies**
   ```yaml
   # Allow metrics access
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-metrics
   spec:
     podSelector:
       matchLabels:
         app: kuber-cron
     ingress:
     - ports:
       - port: 8000
   ```

### 4. Resource Exhaustion

#### Symptoms
- Pod OOMKilled
- High CPU usage
- Slow job execution

#### Diagnosis
```bash
# Check resource usage
kubectl top pod -l app=kuber-cron

# Check pod events
kubectl describe pod -l app=kuber-cron

# Monitor resource trends
kubectl top pod -l app=kuber-cron --containers
```

#### Common Causes and Solutions

1. **Memory Leaks**
   ```python
   # Add memory profiling
   from memory_profiler import profile
   
   @profile
   def run_job():
       # Your job code
   ```

2. **CPU-Intensive Jobs**
   ```python
   # Add CPU usage monitoring
   import psutil
   
   def monitor_cpu():
       cpu_percent = psutil.cpu_percent()
       CPU_USAGE.set(cpu_percent)
   ```

3. **Resource Limits Too Low**
   ```yaml
   # Increase resource limits
   resources:
     requests:
       cpu: "200m"
       memory: "512Mi"
     limits:
       cpu: "1000m"
       memory: "1Gi"
   ```

## Debugging Tools

### 1. Interactive Debugging
```bash
# Start interactive shell
kubectl exec -it deployment/kuber-cron -- /bin/bash

# Run Python debugger
kubectl exec -it deployment/kuber-cron -- python -m pdb src/jobs/your_job.py
```

### 2. Log Analysis
```bash
# Get all logs
kubectl logs deployment/kuber-cron --all-containers

# Follow logs
kubectl logs -f deployment/kuber-cron

# Get logs with timestamps
kubectl logs deployment/kuber-cron --timestamps
```

### 3. Resource Monitoring
```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Monitor resources
kubectl top pods
kubectl top nodes
```

## Prevention Tips

1. **Testing**
   - Test jobs locally before deployment
   - Use staging environment
   - Add unit tests for jobs

2. **Monitoring**
   - Set up alerts for failures
   - Monitor resource usage
   - Check logs regularly

3. **Maintenance**
   - Keep dependencies updated
   - Review and clean logs
   - Monitor disk usage

4. **Documentation**
   - Document job requirements
   - Keep configuration updated
   - Track known issues 