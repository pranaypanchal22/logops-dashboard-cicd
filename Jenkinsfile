pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    // Default values (we’ll overwrite APP_VERSION after checkout)
    APP_VERSION = "local"
    HEALTH_URL  = "http://localhost:8080/health"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        // Compute short commit hash in a way that always works
        script {
          env.APP_VERSION = sh(script: "git rev-parse --short=7 HEAD", returnStdout: true).trim()
        }
        sh '''
          echo "=== Workspace Info ==="
          pwd
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

          echo "=== Resolving requirements file ==="
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

          docker run --rm \
            -v "$PWD:/workspace" -w /workspace \
            python:3.11-slim bash -lc "
              python -m pip install --upgrade pip >/dev/null &&
              pip install -r $REQ &&
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

          # Optional: clean up old stack before redeploy (prevents port conflicts)
          docker compose down || true

          APP_VERSION=${APP_VERSION} docker compose up -d --build
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
          docker compose ps || true
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
  }
}
