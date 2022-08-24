pipeline {
    agent any
    stages {
        stage('Checkout docker repositories'){
            steps{
                sh "echo 'Pulling...  $GIT_BRANCH'"
                sh "printenv"
                cleanWs()
                sh "mkdir docker-common"
                dir('docker-common'){
                    git branch: 'develop', url: 'https://github.com/MaastrichtUniversity/docker-common.git'
                }
                sh "mkdir docker-dev"
                dir('docker-dev'){
                    git branch: 'develop', url: 'https://github.com/MaastrichtUniversity/docker-dev.git'
                }
                withCredentials([
                    file(credentialsId: 'lib-dh', variable: 'libdh')]) {
                       sh "cp \$libdh ./lib-dh.sh"
                }
                sh "ls -ll"
            }
        }
         stage('Clone docker-common externals'){
            steps{
                dir('docker-common'){
                    sh "./rit.sh externals clone"
                }
                dir('docker-common/externals'){
                    sh """
                    mkdir nagios-docker
                    mkdir elastalert-docker
                    mkdir dh-mailer
                    mkdir dh-fail2ban
                    touch dh-fail2ban/fail2ban.env
                    """
                }
            }
        }
        stage('Start proxy'){
            steps{
                dir('docker-common'){
                    sh "#./rit.sh up -d proxy"
                }
            }
        }
        stage('Clone docker-dev externals'){
            steps{
                dir('docker-dev'){
                    sh "./rit.sh externals clone"
                }
                dir('docker-dev/externals'){
                    sh """
                    mkdir dh-faker
                    mkdir dh-mdr
                    mkdir -p epicpid-microservice/docker
                    mkdir irods-frontend
                    mkdir irods-helper-cmd
                    mkdir irods-microservices
                    mkdir irods-open-access-repo
                    mkdir irods-ruleset
                    mkdir rit-davrods
                    mkdir sram-sync
                    """
                }
                dir('docker-dev/externals/irods-helper-cmd'){
                	git branch: 'develop', url:'https://github.com/MaastrichtUniversity/irods-helper-cmd.git'
                }
                dir('docker-dev/externals/irods-microservices'){
                	git branch: 'develop', url:'https://github.com/MaastrichtUniversity/irods-microservices.git'
                }
                dir('docker-dev/externals/irods-ruleset'){
                    sh '''
                    git checkout automated_rule_tests
                    CHECKOUT_BRANCH=$( .github/checkout_correct_branch.sh https://github.com/MaastrichtUniversity/irods-ruleset.git ${GIT_BRANCH} )
                    echo ${CHECKOUT_BRANCH}
                    git checkout ${CHECKOUT_BRANCH}
                    git status
                    '''
//                 	git branch: "${GIT_BRANCH}", url: 'https://github.com/MaastrichtUniversity/irods-ruleset.git'
                }
                dir('docker-dev/externals/sram-sync'){
                	git branch: 'develop', url: 'https://github.com/MaastrichtUniversity/sram-sync.git'
                }
                withCredentials([
                    file(credentialsId: 'irods.secrets.cfg', variable: 'cfg')]) {
                   sh "cp \$cfg docker-dev/irods.secrets.cfg"
                }
            }
        }
        stage('Start iRODS dev env'){
            steps{
                dir('docker-dev'){
                    sh '''
                    CHECKOUT_BRANCH=$( ./externals/irods-ruleset/github/checkout_correct_branch.sh https://github.com/MaastrichtUniversity/idocker-dev.git ${GIT_BRANCH} )
                    echo ${CHECKOUT_BRANCH}
                    git checkout ${CHECKOUT_BRANCH}
                    git status
                    '''
                    //sh "git checkout ${GIT_BRANCH}"
                    sh 'ls -all'
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
