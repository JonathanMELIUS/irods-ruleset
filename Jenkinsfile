pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps {
        echo 'Hello'
        sh 'echo \'Pulling... \' + env.GIT_BRANCH'
        sh 'printenv'
      }
    }

    stage('CleanUp') {
      steps {
        cleanWs(cleanWhenAborted: true, cleanWhenFailure: true, cleanWhenNotBuilt: true, cleanWhenSuccess: true, cleanWhenUnstable: true, deleteDirs: true, cleanupMatrixParent: true, disableDeferredWipeout: true)
      }
    }

  }
}
