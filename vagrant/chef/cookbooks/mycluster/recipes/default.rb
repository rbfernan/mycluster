#
# Cookbook Name:: mycluster
# Recipe:: default
#
#
#TODO Get version from env variables and set file names

directory '/opt/mycluster' do
    owner 'root'
    group 'root'
    mode '0755'
    action :create
end

bash 'Install Docker' do
    user 'root'
    code <<-EOH
    sudo apt-get update -y
    sudo apt install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    EOH
    cwd '/tmp'
end

bash 'Install Docker-compose' do
    user 'root'
    code <<-EOH  
    sudo apt-get install -y docker-compose
    EOH
    cwd '/tmp'
end

# bash 'Install python3' do
#     user 'root'    
#     code <<-EOH
#     sudo apt update -y
#     sudo apt install -y python3-pip
#     EOH
#     cwd '/tmp'
# end