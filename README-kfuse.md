* Create configmap from any topology file you want
  `kubectl create cm trace-load-config-1 --from-file=file-from-cfgmap=topologies/hipster-shop.json`
* Create deployment
  `kubectl apply -f Deployment.yaml`

For generating traces with service labels, use the topology files `35K_spans_per_second_labels-1.json, 35K_spans_per_second_labels-2.json`