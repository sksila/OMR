odoo.define("spc_survey.cam", function (require) {
	'use strict';

	/**
	 * This widget is used for cam column
	 */

	var websiteRootData = require('website.WebsiteRoot');
	var Widget = require('web.Widget');

    const snapModal = $('#snapModal');
	const constraints = {
		video: {width: {min: 300}, height: {min: 300}}
	};
	let video,canvas,snapshot,cameraStream,hiddenInput;
	let paused = false;


	var ColumnCam = Widget.extend({

		// events
		events: {
			'click .play': '_play',
		},

		_play: function (ev) {
			this._startStream();
			snapshot = $(ev.target).closest("td").find('#snapshot'); //used inside _validateSnap
			canvas = $(ev.target).closest("td").find('canvas'); // used inside _validateSnap
			hiddenInput = $(ev.target).closest("div").find("input[type='hidden']"); //get the hidden input to append picture in it
		},

		init: function () {
            this._super.apply(this, arguments);
            //prepare cam's image div
			$('.play').after("<div class='play-area-sub'>" +
				"<canvas id='capture' class='d-none' width='400' height='400'></canvas>" +
				"<div id='snapshot' ></div>" +
				"</div>")
		},

		start: function() {
			var self = this;
            //	screenshot
            jQuery('.screenshot').on('click', function(e) {
                self._screenshot();
            });
            //	retry-snapshot
            jQuery('.retry-snapshot').on('click', function(e) {
                self._retrySnap();
            });
            //	cancel-snapshot
            jQuery('.cancel-snapshot').on('click', function(e) {
                self._stopStreaming();
            });
            //	valid-snapshot
            jQuery('.valid-snapshot').on('click', function(e) {
                self._validateSnap();
            });
		},

		// start Video Stream
		_startStream: function () {
			if ('mediaDevices' in navigator) {
				navigator.mediaDevices.getUserMedia(constraints)
					.then(function (mediaStream) {
						video = document.querySelector('video'); //video tag inside modal
						cameraStream = mediaStream;
						video.srcObject = mediaStream;
						video.play();
					})
					.catch(function (err) {
						console.log("Unable to access camera: " + err);
					});
			} else {
				alert('Your browser does not support media devices.');
				return;
			}
			paused = false;
			this.hideButtons();
		},

		_screenshot: function () {
            video.pause();
            paused = true;
            this.showButtons();
		},


		// stop Streaming
		_stopStreaming: function () {
			if (null != cameraStream) {
				let track = cameraStream.getTracks()[0];
				track.stop();
				video.load();
				cameraStream = null;
				paused = false;
				this.hideButtons();
				snapModal.addClass('d-none');
			}
		},

		_validateSnap: function () {
			if (null != cameraStream && paused == true) {
                var ctx = canvas[0].getContext('2d');
                let img = new Image();
				ctx.drawImage(video, 0, 0, canvas.attr('width'), canvas.attr('height'));
				img.src = canvas[0].toDataURL("image/png");
				img.height = 200;
				img.width = 200;
                snapshot.html('');
                snapshot.append(img);
				paused = false;
				this.hideButtons();
				this._stopStreaming();
				//add img src to the hidden input
				hiddenInput.val(img.src)
			} else {
				this.hideButtons();
				this._stopStreaming();
			}
		},

		_retrySnap: function () {
			if (paused) {
				video.play();
				paused = false;
			}
		},

		showButtons: function () {
			$('.valid-snapshot').removeClass('d-none');
			$('.retry-snapshot').removeClass('d-none');
		},

		hideButtons: function () {
			$('.valid-snapshot').addClass('d-none');
			$('.retry-snapshot').addClass('d-none');
		},


	});

	websiteRootData.websiteRootRegistry.add(ColumnCam, '#wrapwrap');

	return ColumnCam;

});
