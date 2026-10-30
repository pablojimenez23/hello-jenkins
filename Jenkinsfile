pipeline {
    agent any                                   // corre en el propio nodo de Jenkins

    environment {                               // variables que usan todas las etapas
        IMAGE_NAME = 'flask-vuln-app'           // nombre de la imagen de la app
        APP_NAME   = 'flask-app'                // nombre del contenedor desplegado
        NETWORK    = 'devsecops-net'            // red de Docker que comparten la app, SonarQube y ZAP
    }

    // Orden de un CI/CD real: primero las pruebas que no necesitan la app en marcha
    // (Test, SAST y SCA). Solo si pasan sus compuertas se despliega, y recién
    // entonces DAST ataca la app desplegada.
    //
    // Las etapas de seguridad ya están escritas, pero COMENTADAS. En cada paso de la
    // guía descomentas solo la etapa que corresponde: selecciona desde su línea
    // "// stage(" hasta su "// }" final y pulsa Ctrl+/ (Cmd+/ en Mac) en VS Code,
    // o borra a mano el "// " del inicio de cada una de esas líneas.
    // No descomentes las líneas ">>> PASO": son solo marcas para orientarte.
    // Los comentarios que quedan al descomentar (// en Groovy, # en los scripts sh)
    // explican cada línea y no afectan al pipeline.
    stages {
        stage('Build') {                        // construye la imagen de Docker de la app
            steps {
                // Etiqueta la imagen con el número de build: cada ejecución tiene la suya
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }

        stage('Test') {                         // pruebas unitarias dentro de la imagen
            steps {
                // Instala pytest en un contenedor de la imagen y corre la carpeta tests
                sh 'docker run --rm ${IMAGE_NAME}:${BUILD_NUMBER} sh -c "pip install -q pytest && python -m pytest -q tests"'
            }
        }

        // >>> PASO 5: descomenta la etapa SAST - Bandit
        // stage('SAST - Bandit') {                // SAST: revisa el código sin ejecutarlo
        //     steps {                             // lo que hace la etapa
        //         sh '''
        //             # Carpeta de reportes: Jenkins la archiva al final (bloque post)
        //             mkdir -p reports
        //             # Bandit corre en un contenedor de Python que ve tu código:
        //             # --volumes-from jenkins presta la carpeta de trabajo de Jenkins
        //             # y -w "$WORKSPACE" entra a la carpeta de este job
        //             docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim sh -c '
        //                 # Instala Bandit dentro del contenedor
        //                 pip install -q bandit
        //                 # Reporte completo con todas las severidades (|| true: aquí no corta)
        //                 bandit -r app.py -f txt -o reports/bandit.txt || true
        //                 # Muestra el reporte en la Console Output de Jenkins
        //                 cat reports/bandit.txt
        //                 # COMPUERTA: termina con error solo si hay hallazgos High (-lll)
        //                 bandit -r app.py -lll -q > /dev/null
        //             '
        //         '''
        //     }
        // }

        // >>> PASO 6: descomenta la etapa SAST - SonarQube
        // stage('SAST - SonarQube') {             // SAST con más reglas y un panel web
        //     steps {
        //         // Trae el token de la credencial sonar-token a la variable SONAR_TOKEN
        //         withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
        //             sh '''
        //                 # Lanza el escáner de SonarQube en un contenedor:
        //                 #   --network ${NETWORK}       entra a la red donde vive SonarQube
        //                 #   --volumes-from jenkins -w  ve el código de este job
        //                 #   SONAR_HOST_URL             dirección de SonarQube dentro de la red
        //                 #   SONAR_TOKEN                tu token, sin escribirlo en el código
        //                 #   sonar.projectKey           nombre del proyecto en el panel
        //                 #   sonar.sources/exclusions   analiza todo menos tests y reportes
        //                 docker run --rm --user root --network ${NETWORK} \
        //                     --volumes-from jenkins -w "$WORKSPACE" \
        //                     -e SONAR_HOST_URL=http://sonarqube:9000 \
        //                     -e SONAR_TOKEN="$SONAR_TOKEN" \
        //                     sonarsource/sonar-scanner-cli:latest \
        //                     -Dsonar.projectKey=devsecops-lab \
        //                     -Dsonar.sources=. -Dsonar.exclusions=tests/**,reports/**
        //                 # Enlace al panel con los resultados
        //                 echo "Resultados: http://localhost:9000/dashboard?id=devsecops-lab"
        //             '''
        //         }
        //     }
        // }

        // >>> PASO 7: descomenta la etapa SCA - Dependency-Check (va antes de Deploy)
        // stage('SCA - Dependency-Check') {       // SCA: busca CVE en las librerías
        //     steps {
        //         // Trae tu API key de NVD de la credencial nvd-api-key a NVD_API_KEY
        //         withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')]) {
        //             sh '''
        //                 # Carpeta de reportes y limpieza de una ejecución anterior
        //                 mkdir -p reports
        //                 rm -rf sca-deps
        //                 # Instala las librerías de requirements.txt en la carpeta sca-deps,
        //                 # para que Dependency-Check las revise ya instaladas
        //                 docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim \
        //                     pip install -q --root-user-action=ignore --disable-pip-version-check \
        //                     --target sca-deps -r requirements.txt
        //                 # Código de salida de Dependency-Check (0 = sin problemas)
        //                 RC=0
        //                 # Lanza Dependency-Check en un contenedor:
        //                 #   -v dependency-check-data   reusa la base de NVD ya descargada
        //                 #   --scan sca-deps            revisa cada librería instalada
        //                 #   --enableExperimental       activa el analizador de Python
        //                 #   --disableOssIndex          apaga una fuente que pide otra cuenta
        //                 #   --nvdApiKey                tu clave, sin escribirla en el código
        //                 #   --format/--out             deja el reporte HTML y JSON en reports
        //                 #   --failOnCVSS 7             COMPUERTA: falla con un CVE de CVSS 7 o más
        //                 #   || RC=$?                   guarda el resultado sin cortar todavía
        //                 docker run --rm --user root \
        //                     --volumes-from jenkins -w "$WORKSPACE" \
        //                     -v dependency-check-data:/usr/share/dependency-check/data \
        //                     owasp/dependency-check:latest \
        //                     --scan sca-deps --project devsecops-lab \
        //                     --enableExperimental --disableOssIndex \
        //                     --nvdApiKey "$NVD_API_KEY" \
        //                     --format HTML --format JSON --out reports \
        //                     --failOnCVSS 7 || RC=$?
        //                 # Borra la carpeta temporal y recién entonces aplica la compuerta
        //                 rm -rf sca-deps
        //                 exit $RC
        //             '''
        //         }
        //     }
        // }

        stage('Deploy') {                       // despliega la app (solo si todo lo anterior pasó)
            steps {
                sh '''
                    # Crea la red compartida (|| true: si ya existe, sigue)
                    docker network create ${NETWORK} || true
                    # Borra el contenedor de la app del build anterior
                    docker rm -f ${APP_NAME} || true
                    # Levanta la app nueva en la red, publicada en el puerto 5000
                    docker run -d --name ${APP_NAME} --network ${NETWORK} -p 5000:5000 ${IMAGE_NAME}:${BUILD_NUMBER}
                    # Espera hasta 20 s a que /health responda; si responde, la etapa termina bien
                    for i in 1 2 3 4 5 6 7 8 9 10; do
                        docker exec ${APP_NAME} python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" && exit 0
                        sleep 2
                    done
                    # Si nunca respondió, la etapa falla
                    echo "La app no respondió"; exit 1
                '''
            }
        }

        // >>> PASO 8: descomenta la etapa DAST - OWASP ZAP (va después de Deploy)
        // stage('DAST - OWASP ZAP') {             // DAST: ataca la app ya desplegada
        //     steps {
        //         sh '''
        //             # Carpeta de reportes
        //             mkdir -p reports
        //             # Código de salida de ZAP (0 = sin alertas)
        //             RC=0
        //             # Borra un contenedor de ZAP que haya quedado de un build anterior
        //             docker rm -f zap-${BUILD_NUMBER} || true
        //             # Lanza ZAP en modo baseline (pasivo y rápido):
        //             #   --network ${NETWORK}   misma red que la app, la alcanza como flask-app
        //             #   -v zap-wrk-...         volumen donde ZAP deja sus reportes
        //             #   -t http://...:5000/    la app que va a analizar
        //             #   -r / -J                reporte en HTML y en JSON
        //             #   || RC=$?               guarda el resultado sin detener el pipeline
        //             docker run --name zap-${BUILD_NUMBER} --user root --network ${NETWORK} \
        //                 -v zap-wrk-${BUILD_NUMBER}:/zap/wrk \
        //                 ghcr.io/zaproxy/zaproxy:stable \
        //                 zap-baseline.py -t http://${APP_NAME}:5000/ -r zap_report.html -J zap_report.json || RC=$?
        //             # Copia los reportes de ZAP a la carpeta reports del job
        //             docker cp zap-${BUILD_NUMBER}:/zap/wrk/. reports/ || true
        //             # Limpia el contenedor y el volumen de ZAP
        //             docker rm zap-${BUILD_NUMBER}
        //             docker volume rm zap-wrk-${BUILD_NUMBER} || true
        //             # Informa el resultado: esta etapa no bloquea el pipeline
        //             echo "ZAP terminó con código $RC (0 = sin alertas, 1 = fallos, 2 = advertencias). Esta etapa informa, no bloquea."
        //         '''
        //     }
        // }
    }

    post {                                      // se ejecuta al terminar el pipeline
        always {                                // pase lo que pase: guarda los reportes
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success { echo "Pipeline OK: http://localhost:5000" }                       // todo en verde
        failure { echo 'Pipeline falló: abre la etapa en rojo y lee el mensaje.' }  // alguna etapa en rojo
    }
}
