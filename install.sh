
# This is an auto install script for Oracle Autonomous Linux 7.9
# It will configure to automatically run the script using Instance Principals permission
# So ensure you have configured a dynamic group for this instance and that that dynamic group
# has a policy including proper statements. 

# Install needed components and configure crontab

read -p "What is the name of the TagNamespace ? " TagNamespace
read -p "What is the name of the TagKey ? " TagKey
read -p "What time cron should run [0-23] ? " RunHour

echo''
echo '*** run yum update ***'
sudo yum update -y
echo ''
echo '*** install git ***'
sudo yum install git -y
echo ''
echo '*** install oci-cli & oci-python-sdk ***'
python3 -m pip install pip wheel oci oci-cli --user -U
echo ''
echo '*** oci-cli version ***'
python3 -m pip show oci-cli --version | grep Version
echo ''
echo '*** oci-python-sdk version ***'
python3 -m pip show oci --version | grep Version
echo ''
echo '*** git clone from Olygo repo ***'
git clone https://github.com/Olygo/OCI-TagByName.git
echo ''
echo '*** install cron job ***'
cd OCI-TagByName/
crontab -l > ./cron.tmp
echo '0' $RunHour '* * * python3' $PWD'/OCI-TagByName/OCI-TagByName.py -all -tn' $TagNamespace '-tk' $TagKey >> ./cron.tmp
crontab ./cron.tmp
rm ./cron.tmp
crontab -l
echo''