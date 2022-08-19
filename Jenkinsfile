pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                sh "echo 'Pulling...  $GIT_BRANCH'"
                sh 'printenv'
                git branch: "${GIT_BRANCH}", url: 'https://github.com/JonathanMELIUS/irods-ruleset'
            }
        }
        stage('checkout repositories') {
            steps {
                cleanWs()
                git credentialsId: 'GitX1',
                        url: 'git@github.com:MaastrichtUniversity/dh-env.git'
                sh "ls -ll"
            }
        }
        stage('externals clone') {
            steps {
                sh "yes | ./dh.sh externals clone --recursive"
            }
        }
        stage('common proxy') {
            steps {
                dir('docker-common') {
                    sh "#./rit.sh up -d proxy #TODO"
                }
            }
        }
        stage('dependencies') {
            steps {
                dir('docker-dev/externals') {
                    sh "mkdir dh-mdr"
                    sh "mkdir epicpid-microservice"
                }
                dir('docker-dev/externals/irods-ruleset') {
                    sh '''
                    git ls-remote --exit-code --heads ${GIT_URL} ${GIT_BRANCH} &> /dev/null
                    if [ $? -eq 0 ]
                    then
                      git checkout ${GIT_BRANCH}
                      exit 0
                    fi
                    git ls-remote --exit-code --heads ${GIT_URL} ${CHANGE_BRANCH} &> /dev/null
                    if [ $? -eq 0 ]
                    then
                      git checkout ${CHANGE_BRANCH}
                      exit 0
                    fi
                    git checkout ${GIT_COMMIT}
                    '''
                }
                dir('docker-dev/externals/epicpid-microservice') {
                    git credentialsId: 'GitX1', url: 'git@github.com:MaastrichtUniversity/epicpid-microservice.git'
                }
                dir('docker-dev/externals/dh-mdr') {
                    git branch: 'develop', credentialsId: 'GitX1', url: 'git@github.com:MaastrichtUniversity/dh-mdr.git'
                }
                sh "ls -ll"
                withCredentials([
                        file(credentialsId: 'irods.secrets.cfg', variable: 'cfg')
                ]) {
                    sh "cp \$cfg docker-dev/irods.secrets.cfg"
                }
            }
        }
        stage('build & up') {
            steps {
                dir('docker-dev') {
                    sh '''
                    git ls-remote --exit-code --heads ${GIT_URL} ${GIT_BRANCH} &> /dev/null
                    if [ $? -eq 0 ]
                    then
                      git checkout ${GIT_BRANCH}
                      exit 0
                    fi
                    git ls-remote --exit-code --heads ${GIT_URL} ${CHANGE_BRANCH} &> /dev/null
                    if [ $? -eq 0 ]
                    then
                      git checkout ${CHANGE_BRANCH}
                      exit 0
                    fi
                    git checkout ${GIT_COMMIT}
                    '''
                    sh 'git status'
                    sh returnStatus: true, script: './rit.sh down'
                    sh 'echo "Stop existing docker-dev"'
                    sh '''echo "Start iRODS dev environnement"
                        ./rit.sh build irods ires sram-sync
                        ./rit.sh up -d ires sram-sync
                        
                        until docker logs --tail 15 corpus_ires_1 2>&1 | grep -q "Config OK";
                        do
                          echo "Waiting for ires"
                          sleep 10
                        done
                        echo "ires is Done"
                    '''
                }
            }
        }
        stage('Test') {
            steps {
                sh "docker exec -t -u irods corpus_irods_1 /var/lib/irods/.local/bin/pytest /rules/tests"
            }
        }
        stage('CleanUp') {
            steps {
                dir('docker-dev') {
                    sh returnStatus: true, script: './rit.sh down'
                    sh 'echo "Stop docker-dev containers"'
                }
                cleanWs()
            }
        }
    }
}
