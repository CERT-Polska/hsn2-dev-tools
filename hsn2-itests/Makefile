# TODO: make commented code below work to allow easy disabling of particular test suites
#TESTS=""
#TESTS="${TESTS} component_startup_correct.py"
#TESTS="${TESTS} component_startup_incorrect.py"
#TESTS="${TESTS} console.py"
#TESTS="${TESTS} ping.py"
#TESTS="${TESTS} workflows.py"
#TESTS="${TESTS} jobs_incorrect.py"
#TESTS="${TESTS} jobs_correct.py"
#TESTS="${TESTS} simple_job_processing.py"
#TESTS=component_*.py console.py ping.py workflows.py jobs_*.py simple_job_processing.py integration_js-sta.py integration_process_reporters.py integration_service_reporters.py integration_shell-scdbg.py integration_swf-cve.py integration_webclient.py integration_capture-hpc.py integration_thug.py integration_cuckoo.py integration_yara.py
TESTS=component_*.py console.py ping.py workflows.py jobs_*.py simple_job_processing.py integration_js-sta.py integration_process_reporters.py integration_service_reporters.py integration_shell-scdbg.py integration_swf-cve.py integration_webclient.py integration_capture-hpc.py integration_thug.py integration_yara.py

tests:  clean
	@mkdir -p out
	command -v nosetests >/dev/null 2>&1 || { tar zxvf lib/nose-1.1.2.tar.gz -C lib; cd lib/nose-1.1.2; python setup.py install; }
	cp /tmp/tests/lib/hsn2-object-feeder /etc/init.d/; chmod +x /etc/init.d/hsn2-object-feeder
	cp -rf /tmp/tests/lib/cuckooMock /opt/cuckoo
	cp -f /tmp/tests/lib/cuckooMock/cuckoo-mock /etc/init.d/; chmod +x /etc/init.d/cuckoo-mock
	nosetests --with-xunit --xunit-file=out/HSN2-trunk-itests.xml -s ${TESTS}

performance:  clean
	@mkdir -p out
	command -v nosetests >/dev/null 2>&1 || { tar zxvf lib/nose-1.1.2.tar.gz -C lib; cd lib/nose-1.1.2; python setup.py install; }

	nosetests --with-xunit --xunit-file=out/HSN2-trunk-performance-tests.xml -s performance.py

clean:
	rm -rf shunit-* hc.cnf hc.log out /opt/hsn2/file-feeder/*.txt /var/log/hsn2/*

razorback:  clean
	@mkdir -p out
	command -v nosetests >/dev/null 2>&1 || { tar zxvf lib/nose-1.1.2.tar.gz -C lib; cd lib/nose-1.1.2; python setup.py install; }
	cp -f /tmp/tests/lib/clamav/clamav-daemon-for-tests /etc/init.d/; chmod +x /etc/init.d/clamav-daemon-for-tests
	cp -f /tmp/tests/lib/clamav/test.ndb /var/lib/clamav/; chmod 777 /var/lib/clamav/test.ndb
	nosetests -s --with-xunit --xunit-file=out/HSN2-trunk-itests-razorback.xml integration_rb*.py
