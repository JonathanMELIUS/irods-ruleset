pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps {
        echo 'Hello'
        sh 'echo \'Pulling... \' + $GIT_BRANCH'
        sh 'printenv'
        git branch: '$GIT_BRANCH', url: 'https://github.com/JonathanMELIUS/irods-ruleset'
      }
    }
    
    stage('CleanUp') {
      steps {
        cleanWs(cleanWhenAborted: true, cleanWhenFailure: true, cleanWhenNotBuilt: true, cleanWhenSuccess: true, cleanWhenUnstable: true, deleteDirs: true, cleanupMatrixParent: true, disableDeferredWipeout: true)
      }
    }

  }
       
}
