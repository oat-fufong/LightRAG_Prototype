pipeline {
    agent { label 'gpu-agent-2' }
    parameters {
        string(
            name: 'LLM_MODEL',
            defaultValue: 'gpt-4o-mini', 
            description: 'LLM Model to use (e.g., gpt-4o-mini, gpt-4o)'
        )
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'test',
            description: 'Docker container tag as well as output directory'
        )
        string(
            name: 'FILE_TO_PROCESS',
            defaultValue: 'all',
            description: 'List of files to upload and process'
        )
        string(
            name: 'CHECK_INTERVAL_RAW',
            defaultValue: '60',
            description: 'X seconds between check log'
        )
    }
    environment {
        HTTP_PROXY = 'http://10.0.0.3:3128'
        HTTPS_PROXY = 'http://10.0.0.3:3128'
        NO_PROXY = 'localhost,127.0.0.1,metadata.google.internal'
        LIGHTRAG_HOST_PORT = '9621'
        LIGHTRAG_PORT = '9621'
        CONTAINER_NAME = 'lightrag'
        IMAGE_NAME = 'lightrag'
        IMAGE_TAG = "${params.IMAGE_TAG}"
        HOST_INPUT_DIR = '/mnt/filestore/ffl-chatbot/prb' 
        HOST_OUTPUT_DIR = '/home/rapolt/workspace/lightrag-poc/run-lightrag-poc' 
        FILE_TO_PROCESS = "${params.FILE_TO_PROCESS}" 
        CHECK_INTERVAL_RAW = "${params.CHECK_INTERVAL_RAW}"
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
                        credentialsId: 'API_KEY',
                        variable: 'OPENROUTER_API_KEY'
                    )
                ]) {
                    script {
                        sh '''
                        make build \
                            LLM_BINDING=openai \
                            LLM_BINDING_HOST=https://openrouter.ai/api/v1 \
                            LLM_MODEL="${params.LLM_MODEL}" \
                            LLM_BINDING_API_KEY="$OPENROUTER_API_KEY" \
                            EMBEDDING_BINDING=openai \
                            EMBEDDING_BINDING_HOST=https://openrouter.ai/api/v1 \
                            EMBEDDING_MODEL=openai/text-embedding-3-small \
                            EMBEDDING_BINDING_API_KEY="$OPENROUTER_API_KEY" \
                            run
                        '''
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
