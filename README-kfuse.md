* Create configmap from any topology file you want
  `kubectl create cm trace-load-config --from-file=file-from-cfgmap=topologies/hipster-shop.json`
* Create deployment
  `kubectl apply -f Deployment.yaml`
