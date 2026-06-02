pipeline {
    agent { label 'gpu-agent-2' }

    environment {
        HTTP_PROXY = 'http://10.0.0.3:3128'
        HTTPS_PROXY = 'http://10.0.0.3:3128'
        NO_PROXY = 'localhost,127.0.0.1,metadata.google.internal'
        LIGHTRAG_HOST_PORT = '9621'
        LIGHTRAG_PORT = '9621'
        CONTAINER_NAME = 'lightrag'
        IMAGE_NAME = 'lightrag'
        IMAGE_TAG = 'test'
        HOST_INPUT_DIR = '/mnt/filestore/ffl-chatbot/prb' 
        FILE_TO_PROCESS = '1' 
        CHECK_INTERVAL_RAW = '5'
    }

    stages {
        stage('Prepare LightRAG Server & Proxy') {
            steps {
                sh '''
                make clean build \
                '''
            }
        }
        stage('Start Container & Run Script') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'openrouter-api-key',
                        variable: 'OPENROUTER_API_KEY'
                    )
                ]) {
                    script {
                        sh """
                        make build \\
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
        stage('Run Python Script') {
            steps {
                script {
                    sh '''
                    make python
                    '''
                }
            }
        }
    }
    post {
            success{
                sh'''
                make copy stop
                '''
            }
            unsuccessful{
                sh '''
                make stop
                '''
            }
         }
}
