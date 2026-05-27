pipeline {
    agent { label 'gpu' }

    stages {
        stage('Prepare LightRAG Server') {
            steps {
                sh '''
                    make clean build
                '''
            }
        }
        stage('First Run') {
            environment {
                CONTAINER_NAME="lightrag:test"
            }
            steps {
                withCredentials([
                    string(
                        credentialsId: 'openrouter-api-key',
                        variable: 'OPENROUTER_API_KEY'
                    )
                ]) {                        
                    script {
                        sh """
                        make build-${CONTAINER_NAME} \\
                            LLM_BINDING=openai \\
                            LLM_BINDING_HOST=https://openrouter.ai/api/v1 \\
                            LLM_MODEL=deepseek/deepseek-v4-flash \\
                            LLM_BINDING_API_KEY="\$OPENROUTER_API_KEY" \\
                            EMBEDDING_BINDING=openai \\
                            EMBEDDING_BINDING_HOST=https://openrouter.ai/api/v1 \\
                            EMBEDDING_MODEL=openai/text-embedding-3-small \\
                            EMBEDDING_BINDING_API_KEY="\$OPENROUTER_API_KEY" \\
                            run
                        """
                    }
                }
            }
        }
    }
}