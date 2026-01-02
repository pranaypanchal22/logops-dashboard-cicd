pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    APP_VERSION = "local"
    HEALTH_URL  = "http://localhost:8080/health"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.APP_VERSION = sh(script: "git rev-parse --short=7 HEAD", returnStdout: true).trim()
        }

        sh '''
          echo "=== Workspace Info ==="
          echo "PWD: $(pwd)"
          echo "Commit: $(git rev-parse HEAD)"
          echo "APP_VERSION: ${APP_VERSION}"
          echo "=== Files in workspace ==="
          ls -la
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -e
          echo "=== Test Stage ==="
          echo "Host workspace: $(pwd)"
          echo "Host files:"
          ls -la

          # Find requirements (root preferred)
          REQ="requirements.txt"
          if [ ! -f "$REQ" ]; then
            REQ="app/requirements.txt"
          fi

          if [ ! -f "$REQ" ]; then
            echo "ERROR: requirements file not found (expected requirements.txt or app/requirements.txt)"
            echo "Workspace contents:"
            ls -la
            echo "app/ contents (if exists):"
            ls -la app || true
            exit 1
          fi

          echo "Using requirements: $REQ"

          # Run tests in an isolated Python container
          docker run --rm \
            -v "$(pwd):/workspace" -w /workspace \
            python:3.11-slim bash -lc "
              set -e
              echo '=== Inside test container ==='
              echo 'PWD:' && pwd
              echo 'Listing /workspace:' && ls -la /workspace

              # Ensure requirements exist inside container at the mounted path
              test -f /workspace/$REQ || (echo 'REQ NOT FOUND inside container: /workspace/'$REQ && exit 1)

              python -m pip install --upgrade pip >/dev/null
              pip install -r /workspace/$REQ
              pytest -q
            "
        '''
      }
    }

    stage('Build & Deploy') {
      steps {
        sh '''
          set -e
          echo "=== Build & Deploy ==="
          echo "Deploying APP_VERSION=${APP_VERSION}"

          # Avoid port conflicts / stale containers
          docker compose down || true

          # Build + start
          APP_VERSION=${APP_VERSION} docker compose up -d --build

          echo "=== docker compose ps ==="
          docker compose ps
        '''
      }
    }

    stage('Health Check') {
      steps {
        sh '''
          set -e
          echo "=== Health Check ==="
          echo "Checking: ${HEALTH_URL}"

          for i in $(seq 1 30); do
            if curl -fsS "${HEALTH_URL}" > /dev/null; then
              echo "Healthy ✅"
              exit 0
            fi
            echo "Waiting... ($i/30)"
            sleep 2
          done

          echo "Health check failed ❌"
          echo "=== docker compose ps ==="
          docker compose ps || true
          echo "=== docker compose logs (tail) ==="
          docker compose logs --no-color --tail 200 || true
          exit 1
        '''
      }
    }
  }

  post {
    always {
      sh '''
        echo "=== Post: docker compose ps ==="
        docker compose ps || true
      '''
    }
    failure {
      sh '''
        echo "=== Post: docker compose logs (tail) ==="
        docker compose logs --no-color --tail 200 || true
      '''
    }
  }
}
