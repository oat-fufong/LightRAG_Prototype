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
            description: 'Embedding model (OpenRouter format).'
        )
        string(
            name: 'EMBEDDING_DIM',
            defaultValue: '1536',
            description: 'Embedding dimension — must match the model (text-embedding-3-small=1536, bge-m3=1024)'
        )
        string(
            name: 'RUN_TAG',
            defaultValue: 'exp01',
            description: 'Experiment label — used as output directory prefix under HOST_OUTPUT_DIR'
        )
        string(
            name: 'JSON_DATASET',
            defaultValue: '/mnt/filestore/ffl-chatbot/prb/dataset.json',
            description: 'Path to the JSON node dataset on the agent (input to prepare_data.py)'
        )
        string(
            name: 'MAX_NODES',
            defaultValue: '',
            description: 'Max nodes to process per condition (leave blank for all)'
        )
        string(
            name: 'CHECK_INTERVAL_RAW',
            defaultValue: '60',
            description: 'Seconds between ingestion progress checks'
        )
        string(
            name: 'HOST_OUTPUT_DIR',
            defaultValue: '/mnt/filestore/lightrag',
            description: 'Root path on agent where run outputs are saved'
        )
    }
    environment {
        HTTP_PROXY  = 'http://10.0.0.3:3128'
        HTTPS_PROXY = 'http://10.0.0.3:3128'
        NO_PROXY    = 'localhost,127.0.0.1,metadata.google.internal'
        LIGHTRAG_HOST_PORT = '9621'
        LIGHTRAG_PORT      = '9621'
        CONTAINER_NAME     = 'lightrag'
        IMAGE_NAME         = 'lightrag'
        SEP_TAG = "${params.RUN_TAG}-separated"
        COM_TAG = "${params.RUN_TAG}-combined"
        SEP_INPUT = "${WORKSPACE}/experiment/data/separated"
        COM_INPUT = "${WORKSPACE}/experiment/data/combined"
    }

    stages {
        stage('Prepare Data') {
            steps {
                sh 'make clean'
                sh """
                python3 experiment/prepare_data.py \
                    --input '${params.JSON_DATASET}' \
                    --output-dir experiment/data \
                    ${params.MAX_NODES ? "--limit ${params.MAX_NODES}" : ''}
                """
            }
        }

        stage('Run Separated') {
            steps {
                withCredentials([
                    string(credentialsId: 'API_KEY', variable: 'OPENROUTER_API_KEY')
                ]) {
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
                        IMAGE_TAG='${SEP_TAG}' \
                        run
                    """
                }
                sh """
                make python \
                    HOST_INPUT_DIR='${SEP_INPUT}' \
                    FILE_TO_PROCESS=all \
                    CHECK_INTERVAL_RAW='${params.CHECK_INTERVAL_RAW}'
                """
                sh """
                make copy stop \
                    HOST_OUTPUT_DIR='${params.HOST_OUTPUT_DIR}' \
                    IMAGE_TAG='${SEP_TAG}'
                """
                sh """
                mkdir -p '${params.HOST_OUTPUT_DIR}/${SEP_TAG}/results'
                python3 experiment/analyze_cost.py \
                    --cache '${params.HOST_OUTPUT_DIR}/${SEP_TAG}/data/rag_storage/kv_store_llm_response_cache.json' \
                    --output '${params.HOST_OUTPUT_DIR}/${SEP_TAG}/results/cost.json'
                """
            }
        }

        stage('Run Combined') {
            steps {
                sh 'make clean'
                withCredentials([
                    string(credentialsId: 'API_KEY', variable: 'OPENROUTER_API_KEY')
                ]) {
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
                        IMAGE_TAG='${COM_TAG}' \
                        run
                    """
                }
                sh """
                make python \
                    HOST_INPUT_DIR='${COM_INPUT}' \
                    FILE_TO_PROCESS=all \
                    CHECK_INTERVAL_RAW='${params.CHECK_INTERVAL_RAW}'
                """
                sh """
                make copy stop \
                    HOST_OUTPUT_DIR='${params.HOST_OUTPUT_DIR}' \
                    IMAGE_TAG='${COM_TAG}'
                """
                sh """
                mkdir -p '${params.HOST_OUTPUT_DIR}/${COM_TAG}/results'
                python3 experiment/analyze_cost.py \
                    --cache '${params.HOST_OUTPUT_DIR}/${COM_TAG}/data/rag_storage/kv_store_llm_response_cache.json' \
                    --output '${params.HOST_OUTPUT_DIR}/${COM_TAG}/results/cost.json'
                """
            }
        }

        stage('Compare Cost') {
            steps {
                sh """
                python3 experiment/compare_cost.py \
                    --separated '${params.HOST_OUTPUT_DIR}/${SEP_TAG}/results/cost.json' \
                    --combined  '${params.HOST_OUTPUT_DIR}/${COM_TAG}/results/cost.json' \
                    | sudo tee '${params.HOST_OUTPUT_DIR}/${params.RUN_TAG}-comparison.txt'
                """
            }
        }
    }

    post {
        always {
            sh """
            docker stop ${CONTAINER_NAME} || true
            docker rmi --force ${IMAGE_NAME}:${SEP_TAG} || true
            docker rmi --force ${IMAGE_NAME}:${COM_TAG} || true
            """
        }
    }
}
