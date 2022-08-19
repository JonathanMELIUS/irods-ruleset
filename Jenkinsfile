pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps {
        echo 'Hello'
        sh "echo 'Pulling...  $GIT_BRANCH"
        //sh 'printenv'
        git branch: $GIT_BRANCH, url: 'https://github.com/JonathanMELIUS/irods-ruleset'
      }
    }
    
    stage('CleanUp') {
      steps {
        cleanWs()
      }
    }

  }
       
}
