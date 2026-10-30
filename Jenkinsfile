pipeline {
    agent any                                   // corre en el propio nodo de Jenkins

    environment {                               // variables que usan todas las etapas
        IMAGE_NAME = 'flask-vuln-app'           // nombre de la imagen de la app
        APP_NAME   = 'flask-app'                // nombre del contenedor desplegado
        NETWORK    = 'devsecops-net'            // red de Docker que comparten la app, SonarQube y ZAP
    }

    stages {
        stage('Build') {                        // construye la imagen de Docker de la app
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }

        stage('Test') {                         // pruebas unitarias dentro de la imagen
            steps {
                sh 'docker run --rm ${IMAGE_NAME}:${BUILD_NUMBER} sh -c "pip install -q pytest && python -m pytest -q tests"'
            }
        }

        // >>> PASO 5: descomenta la etapa SAST - Bandit
        stage('SAST - Bandit') {                // SAST: revisa el código sin ejecutarlo
            steps {
                sh '''
                    mkdir -p reports
                    docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim sh -c '
                        pip install -q bandit
                        bandit -r app.py -f txt -o reports/bandit.txt || true
                        cat reports/bandit.txt
                        bandit -r app.py -lll -q > /dev/null || true   # TEMPORAL: quitar en el paso 10
                    '
                '''
            }
        }

        // >>> PASO 6: descomenta la etapa SAST - SonarQube
        stage('SAST - SonarQube') {             // SAST con más reglas y un panel web
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        docker run --rm --user root --network ${NETWORK} \
                            --volumes-from jenkins -w "$WORKSPACE" \
                            -e SONAR_HOST_URL=http://sonarqube:9000 \
                            -e SONAR_TOKEN="$SONAR_TOKEN" \
                            sonarsource/sonar-scanner-cli:latest \
                            -Dsonar.projectKey=devsecops-lab \
                            -Dsonar.sources=. -Dsonar.exclusions=tests/**,reports/**
                        echo "Resultados: http://localhost:9000/dashboard?id=devsecops-lab"
                    '''
                }
            }
        }

        // >>> PASO 7: descomenta la etapa SCA - Dependency-Check (va antes de Deploy)
        stage('SCA - Dependency-Check') {       // SCA: busca CVE en las librerías
            steps {
                withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')]) {
                    sh '''
                        mkdir -p reports
                        rm -rf sca-deps
                        docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim \
                            pip install -q --root-user-action=ignore --disable-pip-version-check \
                            --target sca-deps -r requirements.txt
                        RC=0
                        docker run --rm --user root \
                            --volumes-from jenkins -w "$WORKSPACE" \
                            -v dependency-check-data:/usr/share/dependency-check/data \
                            owasp/dependency-check:latest \
                            --scan sca-deps --project devsecops-lab \
                            --enableExperimental --disableOssIndex \
                            --nvdApiKey "$NVD_API_KEY" \
                            --format HTML --format JSON --out reports \
                            --failOnCVSS 11 || RC=$?   # TEMPORAL: volver a 7 en el paso 10
                        rm -rf sca-deps
                        exit $RC
                    '''
                }
            }
        }

        stage('Deploy') {                       // despliega la app (solo si todo lo anterior pasó)
            steps {
                sh '''
                    docker network create ${NETWORK} || true
                    docker rm -f ${APP_NAME} || true
                    docker run -d --name ${APP_NAME} --network ${NETWORK} -p 5000:5000 ${IMAGE_NAME}:${BUILD_NUMBER}
                    for i in 1 2 3 4 5 6 7 8 9 10; do
                        docker exec ${APP_NAME} python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" && exit 0
                        sleep 2
                    done
                    echo "La app no respondió"; exit 1
                '''
            }
        }

        // >>> PASO 8: descomenta la etapa DAST - OWASP ZAP (va después de Deploy)
        stage('DAST - OWASP ZAP') {             // DAST: ataca la app ya desplegada
            steps {
                sh '''
                    mkdir -p reports
                    RC=0
                    docker rm -f zap-${BUILD_NUMBER} || true
                    docker run --name zap-${BUILD_NUMBER} --user root --network ${NETWORK} \
                        -v zap-wrk-${BUILD_NUMBER}:/zap/wrk \
                        ghcr.io/zaproxy/zaproxy:stable \
                        zap-baseline.py -t http://${APP_NAME}:5000/ -r zap_report.html -J zap_report.json || RC=$?
                    docker cp zap-${BUILD_NUMBER}:/zap/wrk/. reports/ || true
                    docker rm zap-${BUILD_NUMBER}
                    docker volume rm zap-wrk-${BUILD_NUMBER} || true
                    echo "ZAP terminó con código $RC (0 = sin alertas, 1 = fallos, 2 = advertencias). Esta etapa informa, no bloquea."
                '''
            }
        }
    }

    post {                                      // se ejecuta al terminar el pipeline
        always {                                // pase lo que pase: guarda los reportes
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success { echo "Pipeline OK: http://localhost:5000" }                       // todo en verde
        failure { echo 'Pipeline falló: abre la etapa en rojo y lee el mensaje.' }  // alguna etapa en rojo
    }
}