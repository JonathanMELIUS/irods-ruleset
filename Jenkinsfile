pipeline {
    agent any
    stages {
        stage('Init') {
            steps {
                sh "echo 'Pulling...  $GIT_BRANCH'"
                sh 'printenv'
                git branch: "${GIT_BRANCH}", url: 'https://github.com/JonathanMELIUS/irods-ruleset'
            }
        }
        stage('Checkout DH-env') {
            steps {
                cleanWs()
                git credentialsId: 'GitX1',
                        url: 'git@github.com:MaastrichtUniversity/dh-env.git'
            }
        }
        stage('Clone externals') {
            steps {
                sh "yes | ./dh.sh externals clone --recursive"
            }
        }
        stage('Up common proxy') {
            steps {
                dir('docker-common') {
                    sh "#./rit.sh up -d proxy #TODO"
                }
            }
        }
        stage('Check dependencies') {
            steps {
                dir('docker-dev/externals') {
                    sh "mkdir dh-mdr"
                    sh "mkdir epicpid-microservice"
                }
                dir('docker-dev/externals/irods-ruleset') {
                    sh '''
                    CHECKOUT_BRANCH=$( ./github/checkout_correct_branch.sh ${GIT_URL} ${GIT_BRANCH} ${CHANGE_BRANCH} )
                    git checkout ${CHECKOUT_BRANCH}
                    '''
                }
                dir('docker-dev/externals/epicpid-microservice') {
                    git credentialsId: 'GitX1', url: 'git@github.com:MaastrichtUniversity/epicpid-microservice.git'
                }
                dir('docker-dev/externals/dh-mdr') {
                    git branch: 'develop', credentialsId: 'GitX1', url: 'git@github.com:MaastrichtUniversity/dh-mdr.git'
                }
                withCredentials([
                        file(credentialsId: 'irods.secrets.cfg', variable: 'cfg')
                ]) {
                    sh "cp \$cfg docker-dev/irods.secrets.cfg"
                }
            }
        }
        stage('Docker dev build & up') {
            steps {
                dir('docker-dev') {
                    sh '''
                    CHECKOUT_BRANCH=$( ./externals/irods-ruleset/github/checkout_correct_branch.sh https://github.com/MaastrichtUniversity/docker-dev.git ${GIT_BRANCH} ${CHANGE_BRANCH} )
                    git checkout ${CHECKOUT_BRANCH}
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
