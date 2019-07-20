
(
	function(){
		"use strict";

		angular.module("WordcountApp", [])
		.controller("WordcountController", ["$scope", "$log", "$timeout", "$http",
			function($scope, $log, $timeout, $http){
				$scope.getResults = function(){
					const getWordCount = (jobId) => {
						let timeout = "";
						const poller = () => {
							$http.get("/results/" + jobId).
								success((data, status, headers, config) => {
									if(status === 202){
										$log.log(data, status);
									}
									else if(status === 200){
										$log.log(data);
										$scope.wordcounts = data;
										$timeout.cancel(timeout);

										return false;
									}
									timeout = $timeout(poller, 2000);
								});
							};
						poller();
					};

					let url = $scope.url;
					$http.post("/start", { url }).
						success((results) => getWordCount(results, $log, $http, $timeout)).
						error((error) => $log.log(error));
				};
			}
		]);
	}()
);
