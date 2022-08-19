GIT_URL=$1
GIT_BRANCH=$2
CHANGE_BRANCH=$3
git ls-remote --exit-code --heads ${GIT_URL} ${GIT_BRANCH} &> /dev/null
if [ $? -eq 0 ]
then
  echo ${GIT_BRANCH}
  #git checkout ${GIT_BRANCH}
  exit 0
fi
git ls-remote --exit-code --heads ${GIT_URL} ${CHANGE_BRANCH} &> /dev/null
if [ $? -eq 0 ]
then
  echo ${CHANGE_BRANCH}
  #git checkout ${CHANGE_BRANCH}
  exit 0
fi
echo "develop"
#echo "automated_rule_tests" #git checkout ${GIT_COMMIT}
#git checkout automated_rule_tests #git checkout ${GIT_COMMIT}