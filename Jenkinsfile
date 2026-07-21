pipeline {
    agent { label 'gpu-agent-5' }
    parameters {
        string(
            name: 'LLM_MODEL',
            defaultValue: 'gpt-4o-mini',
            description: 'LLM Model to use (e.g., gpt-4o-mini, gpt-4o)'
        )
        string(
            name: 'EMBEDDING_MODEL',
            defaultValue: 'openai/text-embedding-3-small',
            description: 'Embedding model (OpenRouter format). Must match the model used at query time.'
        )
        string(
            name: 'EMBEDDING_DIM',
            defaultValue: '1536',
            description: 'Embedding dimension — must match the model (text-embedding-3-small=1536, bge-m3=1024)'
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
        string(
            name: 'HOST_INPUT_DIR',
            defaultValue: '/mnt/filestore/ffl-chatbot/prb' ,
            description: 'Path to mount inputs from'
        )
        string(
            name: 'HOST_OUTPUT_DIR',
            defaultValue: '/mnt/filestore/lightrag',
            description: 'Path to mount outputs to'
        )
        string(
            name: 'QA_FILE',
            defaultValue: 'experiment/qa_dataset.json',
            description: 'Path to Q/A JSON file with source_nodes annotations (relative to workspace)'
        )
        choice(
            name: 'CONDITION',
            choices: ['separated', 'combined'],
            description: 'Experiment condition: separated = one file per article, combined = one file per law'
        )
        string(
            name: 'QUERY_MODE',
            defaultValue: 'mix',
            description: 'LightRAG query mode for retrieval evaluation (local, global, hybrid, naive, mix)'
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
        HOST_INPUT_DIR = "${params.HOST_INPUT_DIR}"
        HOST_OUTPUT_DIR = "${params.HOST_OUTPUT_DIR}"
        FILE_TO_PROCESS = "${params.FILE_TO_PROCESS}"
        CHECK_INTERVAL_RAW = "${params.CHECK_INTERVAL_RAW}"
    }

    stages {
        stage('Prepare LightRAG Server & Proxy') {
            steps {
                sh '''
                make clean
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
                        sh """
                        make build \
                            LLM_BINDING=openai \
                            LLM_BINDING_HOST=https://openrouter.ai/api/v1 \
                            LLM_MODEL='${params.LLM_MODEL}' \
                            LLM_BINDING_API_KEY='${OPENROUTER_API_KEY}' \
                            EMBEDDING_BINDING=openai \
                            EMBEDDING_BINDING_HOST=https://openrouter.ai/api/v1 \
                            EMBEDDING_MODEL='${params.EMBEDDING_MODEL}' \
                            EMBEDDING_DIM='${params.EMBEDDING_DIM}' \
                            EMBEDDING_BINDING_API_KEY='${OPENROUTER_API_KEY}' \
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
        stage('Evaluate Retrieval') {
            steps {
                sh """
                python3 experiment/eval_queries.py \
                    --server http://localhost:${LIGHTRAG_HOST_PORT} \
                    --qa-file '${params.QA_FILE}' \
                    --condition '${params.CONDITION}' \
                    --mode '${params.QUERY_MODE}' \
                    --output experiment/results/${params.IMAGE_TAG}_retrieval.json
                """
            }
        }
        stage('Copy Output & Analyze Cost') {
            steps {
                sh '''
                make copy stop
                '''
                sh """
                python3 experiment/analyze_cost.py \
                    --cache '${HOST_OUTPUT_DIR}/${IMAGE_TAG}/data/rag_storage/kv_store_llm_response_cache.json' \
                    --output experiment/results/${params.IMAGE_TAG}_cost.json
                """
            }
        }
    }
    post {
        always {
            sh '''
            docker stop ${CONTAINER_NAME} || true
            docker rmi --force ${IMAGE_NAME}:${IMAGE_TAG} || true
            '''
        }
    }
}
