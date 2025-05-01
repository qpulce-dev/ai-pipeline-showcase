#!/bin/bash
echo "=== AI Pipeline Debugging Script ==="
echo ""
echo "=== 1. Checking container status ==="
docker ps -a
echo ""
echo "=== 2. Checking API container logs ==="
docker compose logs api --tail 30
echo ""
echo "=== 3. Checking if API container is exposing the port correctly ==="
docker inspect -f "{{range \$p, \$conf := .NetworkSettings.Ports}}{{}} -> {{if \$conf}}{{range \$conf}}{{.HostIp}}:{{.HostPort}}{{end}}{{else}}not exposed{{end}}{{println}}{{end}}" $(docker compose ps -q api)
echo ""
echo "=== 4. Checking network connectivity to API container ==="
API_CONTAINER_IP=$(docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $(docker compose ps -q api))
if [ ! -z "$API_CONTAINER_IP" ]; then
  echo "API container IP: $API_CONTAINER_IP"
  docker run --rm busybox ping -c 3 $API_CONTAINER_IP
else
  echo "Could not determine API container IP!"
fi
echo ""
echo "=== 5. Checking frontend container logs ==="
docker compose logs frontend --tail 30
echo ""
echo "=== 6. Checking environment variables ==="
echo "API container environment:"
docker exec $(docker compose ps -q api) env | grep -E "PORT|HOST"
echo ""
echo "Frontend container environment:"
docker exec $(docker compose ps -q frontend) env | grep -E "PORT|HOST|REACT"
echo ""
echo "=== 7. Checking if the API is actually running inside the container ==="
docker exec $(docker compose ps -q api) ps aux | grep uvicorn
echo ""
echo "=== 8. Checking Docker network configuration ==="
echo "Networks:"
docker network ls
echo ""
echo "AI Pipeline network details:"
docker network inspect ai-pipeline-showcase_ai_pipeline_network
echo ""
echo "=== Debugging complete ==="
echo "To fix connection issues, try:"
echo "1. Restart the containers: docker compose restart api frontend"
echo "2. Rebuild the containers: docker compose up -d --build api frontend"
echo "3. Check for errors in the application code"
echo "4. If everything seems correct, try accessing the API with curl from inside the frontend container:"
echo "   docker exec -it $(docker compose ps -q frontend) curl http://api:8000/health"
