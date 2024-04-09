export_env:
	@conda env export -n mininet-yaml --no-builds > environment.yml

start_vm:
	@multipass launch -n mininet-yaml -m 2G -d 10G -c 2 --cloud-init ./vm/cloud-init.yaml