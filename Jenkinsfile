pipeline {
  agent any

  options { timestamps() }

  environment {
    HEALTH_URL = "http://localhost:8080/health"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          echo "=== Workspace ==="
          pwd
          ls -la
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -e
          echo "=== Test (running in Jenkins container) ==="
          python3 --version
          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pytest -q
        '''
      }
    }

    stage('Build & Deploy') {
      steps {
        sh '''
          set -e
          APP_VERSION=$(git rev-parse --short=7 HEAD)
          echo "APP_VERSION=$APP_VERSION"

          docker compose down || true
          APP_VERSION=$APP_VERSION docker compose up -d --build
          docker compose ps
        '''
      }
    }

    stage('Health Check') {
      steps {
        sh '''
          set -e
          echo "Checking ${HEALTH_URL}"
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
      sh 'docker compose ps || true'
    }
  }
}
