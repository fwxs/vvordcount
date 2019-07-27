(
	function(){
		"use strict";

		angular.module("WordcountApp", [])
		.controller("WordcountController", ["$scope", "$log", "$timeout", "$http",
			function($scope, $log, $timeout, $http){
				$scope.submitButtonText = "Submit";
				$scope.loading = false;
				$scope.urlerror = false;

				$scope.getResults = () => {
					const getWordCount = (jobId) => {
						let timeout = "";
						const poller = () => {
							$http.get("/results/" + jobId).
								then((response) => {
									const {data, status} = response;

									if(status === 202){
										$log.log(data, status);
									}
									else if(status === 200){
										$scope.wordcounts = data;
										$scope.loading = false;
										$scope.submitButtonText = "Submit";
										$scope.wordcounts = data;

										$timeout.cancel(timeout);

										return false;
									}
									timeout = $timeout(poller, 2000);
								},
								(error) => {
									$scope.urlerror = true;
									$scope.submitButtonText = "Submit";
									$scope.loading = false;
								});
							};
						poller();
					};

					let url = $scope.url;
					$http.post("/start", { url }).
						then((results) => {
							getWordCount(results.data, $log, $http, $timeout);
							$scope.urlerror = false;
							$scope.wordcounts = null;
							$scope.loading = true;
							$scope.submitButtonText = "Loading..";
						}, 
						(error) => {
							$scope.urlerror = true;
							$scope.submitButtonText = "Submit";
							$scope.loading = false;
						});
				};
			}
		]);
	}()
);
