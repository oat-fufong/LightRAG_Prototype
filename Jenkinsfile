pipeline {
    agent { label 'gpu' }

    stages {
        stage('Build LightRAG Server') {
            steps {
                sh '''
                    make clean build
                '''
            }
        }
        stage('First Run') {
            environment {
                CONTAINER_NAME=lightrag:test1
            }
            steps {
                script {
                    sh """
                    make build-${CONTAINER_NAME} \\
                        LLM_BINDING=openai \\
                        LLM_BINDING_HOST=https://openrouter.ai/api/v1 \\
                        LLM_MODEL=deepseek/deepseek-v4-flash \\
                        EMBEDDING_BINDING=openai \\
                        EMBEDDING_BINDING_HOST=https://openrouter.ai/api/v1 \\
                        EMBEDDING_MODEL=openai/text-embedding-3-small \\
                        run-${CONTAINER_NAME}
                    """
                }
            }
        }
    }
}
    

