pipeline {
  agent any

  environment {
    // show the deployed version as commit hash
    APP_VERSION = "${env.GIT_COMMIT?.take(7) ?: 'local'}"
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Test') {
      steps {
        sh '''
          docker run --rm -v "$PWD:/workspace" -w /workspace python:3.11-slim bash -lc "
            pip install -r requirements.txt &&
            pytest -q
          "
        '''
      }
    }

    stage('Build & Deploy') {
      steps {
        sh '''
          APP_VERSION=${APP_VERSION} docker compose up -d --build
        '''
      }
    }

    stage('Health Check') {
      steps {
        sh '''
          echo "Waiting for /health..."
          for i in $(seq 1 30); do
            if curl -fsS http://localhost:8080/health > /dev/null; then
              echo "✅ Healthy"
              exit 0
            fi
            sleep 2
          done
          echo "❌ Health check failed"
          docker compose ps
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
