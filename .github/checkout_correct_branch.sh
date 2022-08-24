GIT_URL=$1
GIT_BRANCH=$2

git ls-remote --exit-code --heads ${GIT_URL} ${GIT_BRANCH} &> /dev/null
if [ $? -eq 0 ]
then
  echo ${GIT_BRANCH}
  #git checkout ${GIT_BRANCH}
  exit 0
fi

echo "develop"