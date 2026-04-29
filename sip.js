// ====================
// VARIABLES GLOBALES
// ====================

/* global iceServers:readonly, Janus:readonly, server:readonly, md5:readonly */

var janus = null;
var sipcall = null;
var opaqueId = "siptest-" + Janus.randomString(12);

var localTracks = {}, localVideos = 0,
    remoteTracks = {}, remoteVideos = 0;

var selectedApproach = "secret"; // Modo de autenticación: "secret" o "ha1secret"
var registered = false;
var masterId = null, helpers = {}, helpersCount = 0;
var incoming = null;
var uriserver = ""; // Dirección SIP del servidor
var originalButtons = "";
var lastNumber = "";
var webphoneMinimized = true;
var retryCount = 0;
var maxRetries = 3;

$('#wphone').on('click', function() {
    webphoneMinimized = !webphoneMinimized; // Alternar entre abierto y minimizado
});

// ====================
// INICIALIZACIÓN Y EVENTOS
// ====================

$(document).ready(function() {
	
	originalButtons = $('.botones').html();
	updateAutoAnswerStatus();

  // Estado inicial de la interfaz:
  // - El botón "Llamar" se inicia deshabilitado y con estilo por defecto.
  // - Los botones "Colgar" y "Mute" están ocultos.
  $('.call, .hangup, .mute').hide();
  
  // Inicializar Janus
  Janus.init({
    debug: "all",
    callback: function() {
      // Deshabilitamos el botón de inicio (si lo hay)
      $(this).attr('disabled', true).unbind('click');
      if (!Janus.isWebrtcSupported()) {
        bootbox.alert("No WebRTC support...");
        return;
      }
      // Crear sesión de Janus
      janus = new Janus({
        server: server,
        iceServers: iceServers,
        success: function() {
          // Adjuntar el plugin SIP
          janus.attach({
            plugin: "janus.plugin.sip",
            opaqueId: opaqueId,
            success: function(pluginHandle) {
              $('#details').remove();
              sipcall = pluginHandle;
			  console.log("✅ Plugin SIP adjuntado correctamente.");
              Janus.log("Plugin attached! (" + sipcall.getPlugin() + ", id=" + sipcall.getId() + ")");
              // Registrar al usuario SIP
              registerUsername();
            },
            error: function(error) {
              Janus.error(" -- Error attaching plugin...", error);
              bootbox.alert(" -- Error attaching plugin... " + error);
            },
            consentDialog: function(on) {
              Janus.debug("Consent dialog should be " + (on ? "on" : "off") + " now");
            },
            iceState: function(state) {
              Janus.log("ICE state changed to " + state);
            },
            mediaState: function(medium, on, mid) {
              Janus.log("Janus " + (on ? "started" : "stopped") + " receiving our " + medium + " (mid=" + mid + ")");
            },
            webrtcState: function(on) {
              Janus.log("Janus says our WebRTC PeerConnection is " + (on ? "up" : "down") + " now");
            },
            slowLink: function(uplink, lost, mid) {
              Janus.warn("Janus reports problems " + (uplink ? "sending" : "receiving") +
                " packets on mid " + mid + " (" + lost + " lost packets)");
            },
            onmessage: function(msg, jsep) {
              Janus.debug(" ::: Got a messageX :::", msg);
              // Manejo de errores
              let error = msg["error"];
              if (error) {
                if (!registered) {
                  $('#sip-estatus').text(error);
                } else {
                  sipcall.hangup();
                }
                return;
              }
              let callId = msg["call_id"];
              let result = msg["result"];
              if (result && result["event"]) {
                let event = result["event"];
                if (event === 'registration_failed') {
                  Janus.warn("Registration failed: " + result["code"] + " " + result["reason"]);
                  $('#sip-estatus').text(result["code"] + " " + result["reason"]);
                  $('#status-indicator').css('background-color', 'red');
                  // Mostrar el botón "Llamar" (deshabilitado)
                  $('.call').show().prop('disabled', true)
                             .removeClass('btn-success')
                             .addClass('btn-default');
                  return;
                }
                if (event === 'registered') {
                  Janus.log("Successfully registered as " + result["username"] + "!");
                  if (!registered) {
                    registered = true;
                    masterId = result["master_id"];
					$('#anexo').html('<span title="Registrado" class="status-icon"><i class="mdi mdi-check-circle text-verde"></i> En línea</span>');
                    $('#status-indicator').css('background-color', 'green');
                    $('#estatus').html('<span title="Anexo" class="texto-verde"><i class="mdi mdi-cellphone-basic text-verde mdi-large"></i> ' + result["username"] + '</span>');
                    // Iniciar el temporizador para re-registro
                    // Actualizar el estado del botón "Llamar"
                    updateCallButtonState();
					$('.call').show();
                  }
                } else if (event === 'calling') {
					Janus.log("Waiting for the peer to answer...");
					$('#estatus').html('<strong>Llamando...</strong>');
					// Ocultar botón "Llamar" y mostrar "Colgar" y "Mute"
				    $('.call').hide();
					$('.hangup, .mute').show();
					$('.hangup').addClass('btn-danger');
					$('.mute').addClass('btn-secondary');
                } else if (event === 'incomingcall') {
                  Janus.log("Incoming call from " + result["username"] + "!");
                  sipcall.callId = callId;
                  let doAudio = true, doVideo = true;
                  let offerlessInvite = false;
                  if (jsep) {
                    doAudio = (jsep.sdp.indexOf("m=audio ") > -1);
                    doVideo = (jsep.sdp.indexOf("m=video ") > -1);
                    Janus.debug("Audio " + (doAudio ? "has" : "has NOT") + " been negotiated");
                    Janus.debug("Video " + (doVideo ? "has" : "has NOT") + " been negotiated");
                  } else {
                    Janus.log("This call doesn't contain an offer... we'll need to provide one ourselves");
                    offerlessInvite = true;
                    doVideo = false;
                  }
                  let transfer = "";
                  let referredBy = result["referred_by"];
                  if (referredBy) {
                    transfer = " (referred by " + referredBy + ")";
                    transfer = transfer.replace(/</g, '&lt').replace(/>/g, '&gt');
                  }
                  let rtpType = "";
                  let srtp = result["srtp"];
                  if (srtp === "sdes_optional")
                    rtpType = " (SDES-SRTP offered)";
                  else if (srtp === "sdes_mandatory")
                    rtpType = " (SDES-SRTP mandatory)";
                  //bootbox.hideAll();
                  let extra = offerlessInvite ? " (no SDP offer provided)" : "";
				  
					if (webphoneMinimized) {
						$('#wphone').trigger('click'); // Solo abrir si está minimizado
						webphoneMinimized = false; // Ahora está visible
					}
				  
                  if (aa == '0') { // Si no se activa autoanswer, se pide confirmación
					
                    const txtnumcallid = result["username"];
                    const numcallidarroba = txtnumcallid.split(":");
                    const separnum = numcallidarroba[1];
                    const separnumcallid = separnum.split("@");
                    console.log(separnumcallid[0]);
					
					let message = "Llamada entrante de " + separnumcallid[0] + transfer + rtpType + extra;
					showIncomingCallUI(message, jsep, doAudio, doVideo, offerlessInvite);

                  } else { // Autoanswer
					incoming = null;
					let sipcallAction = offerlessInvite ? sipcall.createOffer : sipcall.createAnswer;
					let tracks = [];
					if (doAudio) tracks.push({ type: 'audio', capture: true, recv: true });
					if (doVideo) tracks.push({ type: 'video', capture: true, recv: true });
					sipcallAction({
					  jsep: jsep,
					  tracks: tracks,
					  success: function(jsep) {
						Janus.debug("Got SDP " + jsep.type + "! audio=" + doAudio + ", video=" + doVideo, jsep);
						sipcall.doAudio = doAudio;
						sipcall.doVideo = doVideo;
						let body = { request: "accept", autoaccept_reinvites: false };
						sipcall.send({ message: body, jsep: jsep });

						// Reproducir alerta local en el navegador
						var alertSound = new Audio('/sistema/sounds/dingdong.wav'); 
						alertSound.volume = 1.0;
						alertSound.play().catch(err => console.error("Error reproduciendo alerta:", err));
						
						// Maximizar webphone automaticamente
							$("#webphone-interface").show();
							webphoneMinimized = false;
					  },
					  error: function(error) {
						Janus.error("WebRTC error:", error);
						bootbox.alert("WebRTC error... " + error.message);
						let body = { request: "decline", code: 480 };
						sipcall.send({ message: body });
					  }
					});
                  }
                } else if (event === 'progress') {
                  Janus.log("There's early media from " + result["username"] + ", waiting for the call!", jsep);
                  if (jsep) {
                    sipcall.handleRemoteJsep({ jsep: jsep, error: doHangup });
                  }
                  //$('#estatus').html('<strong>Timbrando...</strong>');
				  //$('#estatus').html('<span class="texto-verde">' + result["username"] + '</span>');
				  	// Ocultar botón "Llamar" y mostrar "Colgar" y "Mute"
					$('.call').hide();
					$('.hangup, .mute').show();
					$('.hangup').addClass('btn-danger');
					$('.mute').addClass('btn-secondary');
                } else if (event === 'accepted') {
                  Janus.log(result["username"] + " accepted the call!", jsep);
                  $('#estatus').html('<strong>En Llamada</strong>');
                  if (jsep) {
                    sipcall.handleRemoteJsep({ jsep: jsep, error: doHangup });
                  }
                  sipcall.callId = callId;
                  // Actualización de la interfaz en llamada:
                  // Ocultar botón "Llamar" y mostrar "Colgar" y "Mute"
				    $('.call').hide();
					$('.hangup, .mute').show();
					$('.hangup').addClass('btn-danger');
					$('.mute').addClass('btn-secondary');

                  if (actcrm == '1') {
                    window.open('https://www.ipbusiness.pe?idcall=' + result["username"], '_blank');
                  }
                } else if (event === 'updatingcall') {
                  Janus.log("Got re-INVITE");
                  let doAudio = (jsep.sdp.indexOf("m=audio ") > -1);
                  let doVideo = (jsep.sdp.indexOf("m=video ") > -1);
                  let tracks = [];
                  if (doAudio && !sipcall.doAudio) {
                    sipcall.doAudio = true;
                    tracks.push({ type: 'audio', capture: true, recv: true });
                  }
                  if (doVideo && !sipcall.doVideo) {
                    sipcall.doVideo = true;
                    tracks.push({ type: 'video', capture: true, recv: true });
                  }
                  sipcall.createAnswer({
                    jsep: jsep,
                    tracks: tracks,
                    success: function(jsep) {
                      Janus.debug("Got SDP " + jsep.type + "! audio=" + doAudio + ", video=" + doVideo, jsep);
                      let body = { request: "update" };
                      sipcall.send({ message: body, jsep: jsep });
                    },
                    error: function(error) {
                      Janus.error("WebRTC error:", error);
                    }
                  });
                } else if (event === 'message') {
                  let sender = result["displayname"] || result["sender"];
                  let content = result["content"].replace(/</g, '&lt').replace(/>/g, '&gt');
                  toastr.success(content, "Message from " + sender);
                } else if (event === 'info') {
                  let sender = result["displayname"] || result["sender"];
                  let content = result["content"].replace(/</g, '&lt').replace(/>/g, '&gt');
                  toastr.info(content, "Info from " + sender);
                } else if (event === 'notify') {
                  let notify = result["notify"];
                  let content = result["content"];
                  toastr.info(content, "Notify (" + notify + ")");
                } else if (event === 'transfer') {
                  let referTo = result["refer_to"];
                  let referredBy = result["referred_by"] || "an unknown party";
                  let referId = result["refer_id"];
                  let replaces = result["replaces"];
                  let extra = "referred by " + referredBy;
                  if (replaces) extra += ", replaces call-ID " + replaces;
                  extra = extra.replace(/</g, '&lt').replace(/>/g, '&gt');
                  bootbox.confirm("Transfer the call to " + referTo + "? (" + extra + ")",
                    function(result) {
                      if (result) {
                        if (!sipcall.webrtcStuff.pc) {
                          $('#peer').val(referTo).attr('disabled', true);
                          actuallyDoCall(sipcall, referTo, false, referId);
                        } else {
                          let h = -1;
                          if (Object.keys(helpers).length > 0) {
                            for (let i in helpers) {
                              if (!helpers[i].sipcall.webrtcStuff.pc) {
                                h = parseInt(i);
                                break;
                              }
                            }
                          }
                          if (h !== -1) {
                            $('#peer' + h).val(referTo).attr('disabled', true);
                            actuallyDoCall(helpers[h].sipcall, referTo, false, referId);
                          } else {
                            addHelper(function(id) {
                              $('#peer' + id).val(referTo).attr('disabled', true);
                              actuallyDoCall(helpers[id].sipcall, referTo, false, referId);
                            });
                          }
                        }
                      } else {
                        let body = { request: "decline", refer_id: referId };
                        sipcall.send({ message: body });
                      }
                    });
                } else if (event === 'hangup') {
					
                  if (incoming != null) {
					incoming = null;
					$('.botones').empty();
                  }
                  Janus.log("Call hung up (" + result["code"] + " " + result["reason"] + ")!");
                  $('#sip-estatus').html(result["code"] + " " + result["reason"]);
                  $('#estatus').html('<strong>Finalizada</strong>');
                  $('#txtnumeroallama').val('');
                  sipcall.hangup();
					
					// Restaurar botones al estado inicial
					$('.botones').html(
						'<button class="call btn btn-default" onclick="dollamar()"><i class="mdi mdi-phone"></i> Llamar</button>' +
						'<button class="hangup btn btn-danger" onclick="doHangup()" style="display:none;"><i class="mdi mdi-phone-hangup"></i> Colgar</button>' +
						'<button class="mute btn btn-secondary" id="mute" onclick="mute()" style="display:none;"><i class="mdi mdi-microphone"></i> Silenciar</button>'
					);

					$('.call').show();
					$('.hangup, .mute').hide();

					// Re-registra el anexo inmediatamente
					registerUsername();
                } else if (event === 'messagedelivery') {
                  let reason = result["reason"];
                  let code = result["code"];
                  let callid = msg['call_id'];
                  if (code == 200) {
                    toastr.success(`${callid} Delivery Status: ${code} ${reason}`);
                  } else {
                    toastr.error(`${callid} Delivery Status: ${code} ${reason}`);
                  }
                }
              }
            },
            onlocaltrack: function(track, on) {
              Janus.debug("Local track " + (on ? "added" : "removed") + ":", track);
              let trackId = track.id.replace(/[{}]/g, "");
              if (!on) {
                let stream = localTracks[trackId];
                if (stream) {
                  try {
                    let tracks = stream.getTracks();
                    for (let i in tracks) {
                      let mst = tracks[i];
                      if (mst) mst.stop();
                    }
                  } catch(e) {}
                }
                if (track.kind === "video") {
                  localVideos--;
                }
                delete localTracks[trackId];
                return;
              }
              if ($('#videoleft video').length === 0) { }
              if (track.kind === "audio") {
                // Ignorar pista de audio local (para evitar eco)
              } else {
                localVideos++;
                $('#videoleft .no-video-container').remove();
                let stream = new MediaStream([track]);
                localTracks[trackId] = stream;
                Janus.log("Created local stream:", stream);
                $('#videoleft').append('<video class="rounded centered" id="myvideot' + trackId + '" width="100%" height="100%" autoplay playsinline muted="muted"/>');
                Janus.attachMediaStream($('#estadoregistro' + trackId).get(0), stream);
              }
            },
            onremotetrack: function(track, mid, on) {
              Janus.debug("Remote track (mid=" + mid + ") " + (on ? "added" : "removed") + ":", track);
              if (!on) {
                $('#peervideom' + mid).remove();
                if (track.kind === "video") {
                  remoteVideos--;
                  if (remoteVideos === 0) {
                    if ($('#videoright .no-video-container').length === 0) {
                      $('#videoright').append(
                        '<div class="no-video-container">' +
                          '<i class="fa-solid fa-video fa-xl no-video-icon"></i>' +
                          '<span class="no-video-text">No remote video available</span>' +
                        '</div>'
                      );
                    }
                  }
                }
                delete remoteTracks[mid];
                return;
              }
              if (track.kind === "audio") {
                let stream = new MediaStream([track]);
                remoteTracks[mid] = stream;
                Janus.log("Created remote audio stream:", stream);
                $('#videoright').append('<audio class="hide" id="peervideom' + mid + '" autoplay playsinline/>');
                Janus.attachMediaStream($('#peervideom' + mid).get(0), stream);
              } else {
                remoteVideos++;
                $('#videoright .no-video-container').remove();
                let stream = new MediaStream([track]);
                remoteTracks[mid] = stream;
                Janus.log("Created remote video stream:", stream);
                $('#videoright').append('<video class="rounded centered" id="peervideom' + mid + '" width="100%" height="100%" autoplay playsinline/>');
                Janus.attachMediaStream($('#peervideom' + mid).get(0), stream);
              }
            },
            oncleanup: function() {
              Janus.log(" ::: Got a cleanup notification :::");
              $('#videoright').empty();
              $('#dtmf').parent().html("");
              if (sipcall) {
                delete sipcall.callId;
                delete sipcall.doAudio;
                delete sipcall.doVideo;
              }
              localTracks = {};
              localVideos = 0;
              remoteTracks = {};
              remoteVideos = 0;
            }
          });
        },
        error: function(error) {
		  Janus.error(error);
		  retryCount++;
		  if (retryCount <= maxRetries) {
			console.warn("Intentando reconectar... intento #" + retryCount);
			setTimeout(() => location.reload(), 3000);
		  } else {
			console.error("No se pudo conectar con el WebPhone después de varios intentos.");
		  }
        },
        destroyed: function() {
          window.location.reload();
        }
      });
    }
  });
  
  // Actualiza el estado del botón "Llamar" al escribir en el campo
  $('#txtnumeroallama').on('keyup', function () {
    updateCallButtonState();
  });
  
$('#txtnumeroallama').on('keydown', function(e) {
  const teclasPermitidas = [8, 9, 13, 27, 35, 36, 37, 38, 39, 40, 46];
  // Permitir teclas de control
  if (teclasPermitidas.includes(e.keyCode)) return;
  // Permitir números de la fila principal y del teclado numérico
  if ((e.keyCode >= 48 && e.keyCode <= 57) || (e.keyCode >= 96 && e.keyCode <= 105)) return;
  // Permitir '*' y '#' usando e.key
  if (e.key === '*' || e.key === '#') return;
  e.preventDefault();
});
  
  $('#txtnumeroallama').on('keypress', function(e) {
    if (e.keyCode === 13) { 
      if (validarNumeros($(this).val()) === true) {
        dollamar();
      }
    }
  });
  
	function validarNumeros(valor) {
		return (valor !== "" && /^[0-9*#]+$/.test(valor));
	}

}); // Fin document.ready

// ====================
// FUNCIONES DE UTILIDAD Y MANEJO DE LLAMADAS
// ====================

function updateCallButtonState() {
  var number = $('#txtnumeroallama').val().trim();
  if (!registered) {
    $('.call').prop('disabled', true).removeClass('btn-success').addClass('btn-default');
  } else {
    if (number !== "") {
      $('.call').prop('disabled', false).removeClass('btn-default').addClass('btn-success');
    } else {
      $('.call').prop('disabled', true).removeClass('btn-success').addClass('btn-default');
    }
  }
}

function registerUsername() {
	
	if (!janus || !janus.isConnected()) {
        console.error("No hay conexión con Janus. No se puede registrar SIP.");
        return;
    }

    if (!sipcall) {
        console.error("Error: sipcall no está inicializado.");
        return;
    }
	
  let sipserver = "sip:" + sipproxy + ":5060";
  uriserver = sipserver;
  if (!sipserver.startsWith('sip')) {
    console.log("ERROR : Formato inválido de sipserver: " + sipserver);
    return;
  }
  let username = "sip:" + usuariosip + "@" + sipproxy;
  if (!username.includes('@') || !username.startsWith('sip')) {
    console.log("ERROR : Formato inválido de username: " + username);
    return;
  }

  // Remover el token de la clave antes de usarla
  let password = clave.replace(service_account_email, "");
  password = password.substring(2);
  
  if (password === "") {
    console.log("ERROR : La variable password está vacía");
    return;
  }
  let register = {
    request: "register",
    username: username,
    authuser: usuariosip,
    display_name: nomuser
  };
  if (selectedApproach === "secret") {
    register["secret"] = password;
  } else if (selectedApproach === "ha1secret") {
    let sip_user = username.substring(4, username.indexOf('@'));
    let sip_domain = username.substring(username.indexOf('@') + 1);
    register["ha1_secret"] = md5(sip_user + ':' + sip_domain + ':' + password);
  }
  if (sipserver != "") {
    register["proxy"] = sipserver;
    sipcall.send({ message: register });
  } else {
    console.log("Error - No se encontró el sipserver");
    return;
  }
}

function actuallyDoCall(handle, uri, doVideo, referId) {
  handle.doAudio = true;
  handle.doVideo = doVideo;
  let tracks = [{ type: 'audio', capture: true, recv: true }];
  if (doVideo) tracks.push({ type: 'video', capture: true, recv: true });
  handle.createOffer({
    tracks: tracks,
    success: function(jsep) {
      Janus.debug("Got SDP!", jsep);
      let body = { request: "call", uri: uri, autoaccept_reinvites: false };
      if (referId) {
        body["refer_id"] = referId;
      }
      handle.send({ message: body, jsep: jsep });
    },
    error: function(error) {
      Janus.error("WebRTC error...", error);
      bootbox.alert("WebRTC error... " + error.message);
    }
  });
}

function doHangup(ev) {
  let button = ev ? ev.currentTarget.id : "call";
  let helperId = button.split("call")[1];
  helperId = (helperId === "") ? null : parseInt(helperId);
  if (!helperId) {
    // Mostrar botón "Llamar" (deshabilitado) y ocultar "Colgar" y "Mute"
    $('.call').show().prop('disabled', true).removeClass('btn-success').addClass('btn-default');
    let hangup = { request: "hangup" };
    sipcall.send({ message: hangup });
    //sipcall.hangup();
  } else {
    $('#call' + helperId).attr('disabled', true);
    let hangup = { request: "hangup" };
    helpers[helperId].sipcall.send({ message: hangup });
    helpers[helperId].sipcall.hangup();
  }
  // Restaurar estado inicial de la interfaz
  $('.call').show().prop('disabled', true).removeClass('btn-success').addClass('btn-default');
  $('.hangup, .mute').hide();
  $('#txtnumeroallama').val('');
  $('#estatus').val("");
  $('#sip-estatus').html("");
}

function addHelper(helperCreated) {
  helperCreated = (typeof helperCreated == "function") ? helperCreated : Janus.noop;
  helpersCount++;
  let helperId = helpersCount;
  helpers[helperId] = { id: helperId, localTracks: {}, localVideos: 0, remoteTracks: {}, remoteVideos: 0 };
  $('.footer').before(
    '<div class="container" id="sipcall' + helperId + '">' +
      '<div class="row">' +
        '<div class="col-md-6 container">' +
          '<span class="badge bg-info">Helper #' + helperId +
            '<i class="fa-solid fa-rectangle-xmark" id="rmhelper' + helperId + '" style="cursor: pointer;" title="Remove this helper"></i>' +
          '</span>' +
        '</div>' +
        '<div class="col-md-6 container" id="phone' + helperId + '">' +
          '<div class="input-group mt-1 mb-1">' +
            '<span class="input-group-text"><i class="fa-solid fa-phone"></i></span>' +
            '<input disabled class="form-control" type="text" placeholder="SIP URI to call (e.g., sip:1000@example.com)" autocomplete="off" id="peer' + helperId + '" onkeypress="return checkEnter(this, event, ' + helperId + ');">' +
          '</div>' +
          '<button disabled class="btn btn-success mb-1" autocomplete="off" id="call' + helperId + '">Call</button>' +
          '<input autocomplete="off" id="dovideo' + helperId + '" type="checkbox">Use Video</input>' +
        '</div>' +
      '</div>' +
      '<div id="videos' + helperId + '" class="row mt-2 mb-2 hide">' +
        '<div class="col-md-6">' +
          '<div class="card">' +
            '<div class="card-header"><span class="card-title">You</span></div>' +
            '<div class="card-body" id="videoleft' + helperId + '"></div>' +
          '</div>' +
        '</div>' +
        '<div class="col-md-6">' +
          '<div class="card">' +
            '<div class="card-header"><span class="card-title">Remote UA</span></div>' +
            '<div class="card-body" id="videoright' + helperId + '"></div>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>'
  );
  $('#rmhelper' + helperId).click(function() {
    let hid = $(this).attr('id').split("rmhelper")[1];
    console.log("Eliminar helper: " + hid);
    removeHelper(hid);
  });
  janus.attach({
    plugin: "janus.plugin.sip",
    opaqueId: opaqueId,
    success: function(pluginHandle) {
      helpers[helperId].sipcall = pluginHandle;
      Janus.log("[Helper #" + helperId + "] Plugin attached! (" + helpers[helperId].sipcall.getPlugin() + ", id=" + helpers[helperId].sipcall.getId() + ")");
      helpers[helperId].sipcall.send({
        message: {
          request: "register",
          type: "helper",
          username: $('#username').val(),
          master_id: masterId
        }
      });
    },
    error: function(error) {
      Janus.error("[Helper #" + helperId + "] -- Error attaching plugin...", error);
      bootbox.alert(" -- Error attaching plugin... " + error);
      removeHelper(helperId);
    },
    consentDialog: function(on) {
      Janus.debug("[Helper #" + helperId + "] Consent dialog should be " + (on ? "on" : "off") + " now");
    },
    iceState: function(state) {
      Janus.log("[Helper #" + helperId + "] ICE state changed to " + state);
    },
    mediaState: function(medium, on, mid) {
      Janus.log("[Helper #" + helperId + "] Janus " + (on ? "started" : "stopped") + " receiving our " + medium + " (mid=" + mid + ")");
    },
    webrtcState: function(on) {
      Janus.log("[Helper #" + helperId + "] Janus says our WebRTC PeerConnection is " + (on ? "up" : "down") + " now");
      $("#videoleft" + helperId).parent().unblock();
    },
    slowLink: function(uplink, lost, mid) {
      Janus.warn("Janus reports problems " + (uplink ? "sending" : "receiving") +
        " packets on mid " + mid + " (" + lost + " lost packets)");
    },
    onmessage: function(msg, jsep) {
      // Lógica similar para helpers si se necesita
    },
    onlocaltrack: function(track, on) {
      // Implementar manejo de pistas locales para helpers si es necesario
    },
    onremotetrack: function(track, mid, on) {
      // Implementar manejo de pistas remotas para helpers si es necesario
    },
    oncleanup: function() {
      $('#videoleft' + helperId).empty();
      $('#videos' + helperId).addClass('hide');
      $('#dtmf' + helperId).parent().html("Remote UA");
      if (helpers[helperId] && helpers[helperId].sipcall) {
        delete helpers[helperId].sipcall.callId;
        delete helpers[helperId].sipcall.doAudio;
        delete helpers[helperId].sipcall.doVideo;
      }
      if (helpers[helperId]) {
        helpers[helperId].localTracks = {};
        helpers[helperId].localVideos = 0;
        helpers[helperId].remoteTracks = {};
        helpers[helperId].remoteVideos = 0;
      }
    }
  });
}

function removeHelper(helperId) {
  if (helpers[helperId] && helpers[helperId].sipcall) {
    helpers[helperId].sipcall.detach();
    delete helpers[helperId];
  }
}

function revisaEnter(field, event) {
  let theCode = event.keyCode || event.which || event.charCode;
  if (theCode == 13) {
    dollamar();
    console.log("PRESIONO ENTER");
  } else {
    const allowedChars = /[0-9*#]/;
    if (!allowedChars.test(event.key)) {
      event.preventDefault();
    }
  }
}

function dollamar(ev) {
	var colorRgb = $('#status-indicator').css('backgroundColor');
	var colorHex = rgbToHex(colorRgb);
	var number = $('#txtnumeroallama').val().trim();
	if (colorHex == '#ff0000') {
		console.log("Webphone no Registrado");
		$('#sip-estatus').html('<strong>No Registrado</strong>');
		return;
	}
	if ($('#txtnumeroallama').val().trim() == '') {
		console.log("Campo vacío: no se realiza llamada");
		$('#sip-estatus').html('<strong>Ingrese un número a llamar</strong>');
		return;
	}
    if (number === '') {
        console.log("Campo vacío, no se puede llamar.");
        $('#sip-estatus').html('<strong>Ingrese un número a llamar</strong>');
        return;
    }
  
	lastNumber = number;
  $('#sip-estatus').html('');
  let button = ev ? ev.currentTarget.id : "btnllamar";
  let helperId = button.split("btnllamar")[1];
  helperId = (helperId === "") ? null : parseInt(helperId);
  let handle = helperId ? helpers[helperId].sipcall : sipcall;
  let prefix = helperId ? ("[Helper #" + helperId + "]") : "";
  let suffix = helperId ? ("" + helperId) : "";
  let usernametocall = $('#txtnumeroallama').val();
  const splitnumbercall = uriserver.split(":");
  let uridocall = "sip:" + $('#txtnumeroallama').val() + "@" + splitnumbercall[1];
  console.log("DATALlamar: " + usernametocall + " | UriServer: " + uridocall + " | usuariosip: " + usuariosip);
  let doVideo = false;
  Janus.log(prefix + "This is a SIP " + (doVideo ? "video" : "audio") + " call (dovideo=" + doVideo + ")");
  actuallyDoCall(handle, uridocall, doVideo);
}

function rgbToHex(rgb) {
  var parts = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
  if (!parts) return rgb;
  function toHex(n) {
    var hex = parseInt(n).toString(16);
    return hex.length === 1 ? "0" + hex : hex;
  }
  return "#" + toHex(parts[1]) + toHex(parts[2]) + toHex(parts[3]);
}

function updateAutoAnswerStatus() {
    var statusText = (aa === '1') ? '<span title="Auto Respuesta Activado" class="status-icon"><i class="mdi mdi-phone-incoming texto-verde mdi-large"></i> AA</span>' : "";
    document.getElementById("auto-answer-status").innerHTML = statusText;
}

function showIncomingCallUI(message, jsep, doAudio, doVideo, offerlessInvite) {
  // Oculta los botones originales
  //
  //$('.call, .hangup, .mute').hide();
  $('.call').hide();
  
  // Actualiza un elemento (por ejemplo, #sip-estatus) para mostrar el mensaje de la llamada entrante
  $('#sip-estatus').text(message);
  
  // Reemplaza el contenido del div con clase "botones" por los botones "Answer" y "Decline"
  $('.botones').html(
    '<button id="btnAnswer" class="btn btn-success btn-block"><i class="mdi mdi-phone-in-talk"></i> Contestar</button>' +
    '<button id="btnDecline" class="btn btn-danger btn-block"><i class="mdi mdi-phone-missed"></i> Rechazar</button>'
  );
  
  // Asigna el callback para el botón "Answer"
  $('#btnAnswer').click(function() {
    // Limpia la interfaz de llamada entrante
    $('.botones').empty();
    // Llama a la función correspondiente para contestar
    let sipcallAction = offerlessInvite ? sipcall.createOffer : sipcall.createAnswer;
    let tracks = [];
    if (doAudio) tracks.push({ type: 'audio', capture: true, recv: true });
    if (doVideo) tracks.push({ type: 'video', capture: true, recv: true });
    sipcallAction({
      jsep: jsep,
      tracks: tracks,
      success: function(jsep) {
        Janus.debug("Got SDP " + jsep.type + "! audio=" + doAudio + ", video=" + doVideo, jsep);
        sipcall.doAudio = doAudio;
        sipcall.doVideo = doVideo;
        let body = { request: "accept", autoaccept_reinvites: false };
        sipcall.send({ message: body, jsep: jsep });
		$('.botones').html(originalButtons);
		$('.hangup, .mute').show();
      },
      error: function(error) {
        Janus.error("WebRTC error:", error);
        alert("WebRTC error... " + error.message);
        let body = { request: "decline", code: 480 };
        sipcall.send({ message: body });
      }
    });
  });
  
  // Asigna el callback para el botón "Decline"
  $('#btnDecline').click(function() {
    $('.botones').empty();
    let body = { request: "decline" };
    sipcall.send({ message: body });
	
    // Restaura la interfaz original (por ejemplo, mostrando el botón "Llamar")
    $('.botones').html(originalButtons);
	$('.call').show();
    updateCallButtonState();
  });
}

function checkSIPStatus() {
    if (!janus || !janus.isConnected()) {
        console.error("No hay conexión con Janus. Intentando reconectar...");
        return;
    }

    if (!sipcall) {
        console.error("Error: sipcall no está inicializado.");
        return;
    }

    let registerCheck = { request: "info" }; // Usamos "info" en lugar de "register"

    //console.log(" Enviando solicitud de estado SIP a Janus:", registerCheck);

    sipcall.send({
        message: registerCheck,
        success: function(response) {
            //console.log("Respuesta recibida de SIP:", response);

            /*if (!response || typeof response.result === "undefined") {
                console.error("Error: Respuesta inválida de SIP", response);
                return;
            }

            if (response.result.event !== "registered") {
                console.log("El anexo no está registrado. Intentando reconectar...");
                registerUsername();
            } else {
                console.log("El anexo sigue registrado.");
            }*/
        },
        error: function(error) {
            console.error("Error en la verificación del estado SIP:", error);
        }
    });
}


// Verificar estado SIP cada 60 segundos
//setInterval(checkSIPStatus, 60000);


