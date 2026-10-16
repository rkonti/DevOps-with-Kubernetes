# Monitoring

Prometheus + Grafana, with Loki and Alloy collecting the logs of every pod.

```sh
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts

kubectl create namespace prometheus
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n prometheus -f kube-prometheus-stack-values.yaml

kubectl create namespace loki-stack
helm install loki grafana/loki -n loki-stack -f loki-values.yaml
helm install alloy grafana/alloy -n loki-stack -f alloy-values.yaml
```

Open Grafana:

```sh
kubectl -n prometheus get secret kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
kubectl -n prometheus port-forward svc/kube-prometheus-stack-grafana 3000:80
```

In Explore, pick the Loki datasource. To see the todos the backend has rejected:

```
{namespace="project", app="todo-backend"} |= "Rejected"
```
