var selected_base = '2m';
var selected_texture = 'whiterivet';

var path = new Array();
// height, radius
path[0] = [0.0,1.0];
path[1] = [3.0,1.0];
path[2] = [3.6,0.6];
path[3] = [4.0,0.0];

var cuts = new Array();
cuts[0] = 0.0;
cuts[1] = 2.0;
cuts[2] = 999.0;

var mouse_status = "hover";

var choice_cut = -1; //the cut thats being hovered over
var choice_point = -1; // the point thats being hovered over
var choice_side = -1; // which side that point is on, -1=left, 1=right
                    
var cut_bounds = {
    "above":-1,
    "below":-1
};
                    
var point_bounds = {
    "above":-1,
    "below":-1,
    "radmin":-1,
    "radmax":-1
};


var basewidth = {
	'hm':0.5,
	'1m':1.0,
	'2m':2.0,
	'3m':3.0,
	'5m':5.0,
}

var candidate_point = null;
var candidate_cut = null;
var zoom = 180.0;
var send_button_state = 'send';
var kitid = null;
var zoomrate = 0.008;
var snap = false;
var showMeasures = false

var refimage = new Image();
var showPicture = false;
refimage.onload = function() {
    //enable show ref tickbox
    };
// image begins to load when this is set
refimage.src = 'images/refm.png';

function send_order(){
    sections = new Array();
    
    var p=0;
    var last_cutpoint;
    for(var s=1; s<cuts.length; s++){
    	var vin = true;
    	sect_prof = new Array();
    	if (s>1){
	    	sect_prof.push(last_cutpoint)
    	}
    	while(p<path.length && vin){
	    	console.log('cutssss',path[p][0],cuts[s])
			if (path[p][0] > cuts[s]){
				// just overstepped a cut
				// the height val of the final point in this section is the cut
				// interpolate the rad val from the points that straddle the cut
				var x0 = path[p-1][1];
				var x1 = path[p][1];
				var y0 = path[p-1][0];
				var y1 = path[p][0];
				var cy = cuts[s];
				var cx = (cy-y0)/(y1-y0)*(x1-x0)+x0; // linear interpolation
				last_cutpoint = new Array(cy,cx);
				console.log("interpolate",last_cutpoint)
				sect_prof.push(last_cutpoint);
				vin = false;
			} else {
				console.log("regular point",path[p])
				sect_prof.push(path[p]);
				p++;
				if (p >= path.length){
					break;
				}
			}
		}
		var capped = (s==(cuts.length-1));
		if (sect_prof.length > 1){
			sections.push({
				"capped":capped,
				"profile":sect_prof
			});
		}
		console.log("finish section",sections.length-1)
		
    }

    var orderjson = JSON.stringify({
        "texture":selected_texture,
        "base-size":selected_base,
        "sections": sections
    });    console.log("I am about to POST this:\n\n" + orderjson);
    $.post(
        "http://nathannifong.com:8009",
        orderjson,
        function(data) {
            console.log("Response: " + data);
            kitid = data.split('\n')[1].split('=')[1];
        }
    );
    
}

function newbasewidth(sizeinmeters){
	path[0] = [0.0,sizeinmeters/2];
	draw(-1,-1);
}

function setup(){

	$('#sendbutton').hover(function(){
		if (send_button_state == 'send' || send_button_state == 'download'){
			$(this).css('background-color','rgb(200,200,255)');
		}
	},
	function(){
		if (send_button_state == 'send' || send_button_state == 'download'){
			$(this).css('background-color','rgb(255,255,255)');
		}
	});
	
	$('#sendbutton').click(function(){
		if (send_button_state == 'send'){
			send_order();
			$(this).css('background-color', 'rgb(240,240,240)');
			$(this).css('color', 'rgb(90,90,90)');
			$(this).css('font-size', '10pt');
			$(this).css('border', 'none');
			$(this).html('processing...');
			send_button_state = "disabled";
			setTimeout(function() {
				send_button_state = "download";
		   		$('#sendbutton').css('background-color', 'rgb(255,255,255)');
		    	$('#sendbutton').css('color', 'rgb(110,80,240)');
		    	$('#sendbutton').css('font-size', '18pt');
		    	$('#sendbutton').css('border', '2px rgb(100,100,100) solid');
		    	$('#sendbutton').html('Download');
	    	}, 1400);	
		} else if (send_button_state == 'download'){
			send_button_state = "send";
			document.location = 'dev_downloads/fairing_kit_'+kitid+'.zip';
			$(this).css('background-color','rgb(255,255,255)');
			$(this).css('color','rgb(212,95,0)');
		    $(this).html('Send');
			
		}
		console.log("send_button_state "+send_button_state);
	});

	$('#2m').css('background-color','rgb(255,245,120)');

	$('.togg').hover(
		function(){
			$(this).css('background-color','rgb(200,200,255)');
		},
		function(){
			if ($(this).attr('id') == selected_base){
				$(this).css('background-color','rgb(255,245,120)')
			} else {
				$(this).css('background-color','rgb(255,255,255)');
			}
		}
	);
	
	$('.textogg').hover(
		function(){
			$(this).css('border-color','rgb(200,200,255)');
		},
		function(){
			if ($(this).attr('id') == selected_texture){
				$(this).css('border-color','rgb(255,245,120)')
			} else {
				$(this).css('border-color','rgb(100,100,100)');
			}
		}
	);
	
	$('.togg').click(function(){
		selected_base = $(this).attr('id');
		$('.togg').css('background-color','rgb(255,255,255)');
		$(this).css('background-color','rgb(255,245,120)')
		newbasewidth(basewidth[selected_base]);
	});
	
	$('.textogg').click(function(){
		selected_texture = $(this).attr('id');
		$('.textogg').css('border-color','rgb(100,100,100)');
		$(this).css('border-color','rgb(255,245,120)')
	});
	
	var zoomRepeater;
	
	$('#zoom_in').mousedown(function(){
		zoomRepeater = setInterval(function(){
			zoom *= (1-zoomrate);
			draw(-1,-1);
		},50);
	});
	$('#zoom_in').mouseup(function(){
		clearInterval(zoomRepeater);
	});
	
	$('#zoom_out').mousedown(function(){
		zoomRepeater = setInterval(function(){
			zoom *= (1+zoomrate);
			draw(-1,-1);
		},50);
	});
	$('#zoom_out').mouseup(function(){
		clearInterval(zoomRepeater);
	});

    var canvas = document.getElementById("usp");
    var mouseX,mouseY;
    
    canvas.addEventListener('keydown', function(evt) {
        if (evt.keyCode == 88){
            // x was pressed. delete the thing being held
            if (mouse_status == "holding_point"){
                delete_point();
            } else if (mouse_status == "holding_cut"){
                delete_cut();
            }
        }
        draw(mouseX,mouseY);
    }, false);
    
    canvas.addEventListener('mousemove', function(evt) {
        canvas.focus();
        var rect = canvas.getBoundingClientRect(), root = document.documentElement;
        // relative mouse position
        //console.log(rect.top, rect.left)
        mouseX = evt.clientX - rect.left;// - root.scrollTop;
        mouseY = evt.clientY - rect.top;// - root.scrollLeft;
        if (mouse_status=="hover"){
            hover_cuts(mouseX,mouseY);
            hover_points(mouseX,mouseY);
        } else if (mouse_status=="holding_cut"){
            move_held_cut(mouseX,mouseY);
        } else if (mouse_status=="holding_point"){
            move_held_point(mouseX,mouseY);
        }
        draw(mouseX,mouseY);
    }, false);
    
    canvas.addEventListener('mouseup', function(evt) {
        var rect = canvas.getBoundingClientRect(), root = document.documentElement;
        // relative mouse position
        //console.log(rect.top, rect.left)
        mouseX = evt.clientX - rect.left;// - root.scrollTop;
        mouseY = evt.clientY - rect.top;// - root.scrollLeft;

        if (mouse_status == "hover"){
            if (mouseX < 20){
                if (choice_cut != -1){
                    cut_bounds = {
                        "above":cuts[choice_cut+1],
                        "below":cuts[choice_cut-1]
                    };
                    mouse_status = "holding_cut";
                    console.log("choice_cut ",choice_cut);
                } else if (candidate_cut){
                    choice_cut = candidate_cut['above'];
                    cuts.splice(choice_cut, 0, candidate_cut['height']);
                    cut_bounds = {
                        "above":cuts[choice_cut+1],
                        "below":cuts[choice_cut-1]
                    };
                    candidate_cut = null;
                    mouse_status = "holding_cut"
                }
            } else {
                if (choice_point != -1 ){
                	if (choice_point == path.length-1){
                		point_bounds = {
	                        "above": 9999,
	                        "below": path[choice_point-1][0],
	                        "radmin": 0.0,
	                        "radmax": 0.0
	                    };
                	} else {
	                    point_bounds = {
	                        "above": path[choice_point+1][0],
	                        "below": path[choice_point-1][0],
	                        "radmin": 0.0,
	                        "radmax": 9990.0
	                    };
                    }
                    mouse_status = "holding_point"
                } else if (candidate_point) {
                    // create a new point and splice it into the path
                    choice_point = candidate_point['above'];
                    path.splice(choice_point, 0, [candidate_point['height'], candidate_point['rad']]);
                    point_bounds = {
                        "above": path[choice_point+1][0],
                        "below": path[choice_point-1][0],
                        "radmin": 0.0,
                        "radmax": 9999.0
                    };
                    candidate_point = null
                    mouse_status = "holding_point"
                }
            }
        } else if (mouse_status == "holding_cut") {
            mouse_status = "hover";
        } else if (mouse_status == "holding_point") {
            mouse_status = "hover";
        }
        console.log(mouse_status)
        draw(mouseX,mouseY);
    }, false);

    
    draw(-100,0);
}

function delete_point(){
	if (choice_point != path.length-1){
    	path.splice(choice_point,1);
    	choice_point=-1;
    	mouse_status="hover"
    }
}

function delete_cut(){
    cuts.splice(choice_cut,1);
    choice_cut=-1;
    mouse_status="hover"
}

function hover_cuts(mouseX,mouseY){
    choice_cut = -1
    var closest = -1;
    var disclo = 9999;
    candidate_cut = null;
    which_above = null
    if (mouse_status=="hover" && mouseX<20){
        for(var i=0; i<cuts.length; i++){
            var cvco = fco_to_cvco(0, cuts[i]);
            if (which_above==null && cvco.y<mouseY){
                which_above = i;
            }
            // if not first or last cut (special)
            if (i!=0 && i!=(cuts.length-1)){
                var dy = Math.abs(mouseY-cvco.y);
                if (dy<10){
                    if (dy < disclo){
                        disclo = dy;
                        closest = i;
                    }
                }
            }
        }
        choice_cut = closest;
        if (choice_cut == -1){
            tgt = cvco_to_fco(mouseX,mouseY);
            if (tgt['height'] < cuts[cuts.length-1]){
                candidate_cut = {
                    'height':tgt['height'],
                    'above':which_above
                };
            }
        }
    }
}

function hover_points(mouseX,mouseY){
    // figure out which point we are hovering closest to
    choice_point = -1
    var closest = -1;
    var disclo = 9999;
    var clomu = 1; // which side was the closest one detected on
    // destroy candidate
    candidate_point = null;
    if (mouseX>20){
        for(var i=1; i<path.length; i++){
            for(var mu=1; mu>=-1; mu-=2){
                co = fco_to_cvco(mu*path[i][1], path[i][0]);
                kd = Math.sqrt( Math.pow(mouseX-co.x,2) + Math.pow(mouseY-co.y,2) );
                if (kd<12 && kd < disclo){
                    disclo = kd;
                    closest = i;
                    clomu = mu;
                }
            }

            var cvco = fco_to_cvco(path[i][1], path[i][0]);
            if (cvco.y < mouseY){
                // hovering above pco and below cvco
                var pco = fco_to_cvco(path[i-1][1], path[i-1][0]);
                var true_xpos = (mouseY - cvco.y) / (cvco.y - pco.y) * (cvco.x - pco.x) + cvco.x
                // is it close enough?
                left_d = Math.abs(true_xpos-mouseX)
                //other side
                var tgt = cvco_to_fco(true_xpos,mouseY);
                right_d = Math.abs(fco_to_cvco(-1*tgt.rad, tgt.height)['x'] - mouseX);
                
                if (left_d < 25 || right_d < 25 ){
                    // create candidate
                    candidate_point = {
                        "above":i,
                        "below":i-1,
                        "rad":tgt['rad'],
                        "height":tgt['height']
                    }
                }
                break;
            }

        }
    }
    choice_point = closest;
    choice_side = clomu;
    if (choice_point != -1){
        candidate_point = null;
    }
}

function move_held_cut(mouseX,mouseY){
    console.log('move held cut',choice_cut)
    if (choice_cut != -1){
        var margin = 0.01;
        var tgt = cvco_to_fco(mouseX, mouseY);
        if ( (cut_bounds["above"]-margin)>tgt.height && tgt.height>(cut_bounds["below"]+margin) ){
            cuts[choice_cut] = tgt.height;
        }
    }
}

function move_held_point(mouseX,mouseY){
    if (choice_point != -1){
        console.log('moving point',choice_point)
        var margin = 0.01;
        var tgt = cvco_to_fco(mouseX, mouseY);
        tgt['rad'] = Math.abs(tgt['rad']);
        
        if(snap){
        	tgt['rad'] = Math.round(tgt['rad']*20)/20;
        	tgt['height'] = Math.round(tgt['height']*20)/20;
        }
        
        if (choice_point == path.length-1){
        	if (tgt['height'] > point_bounds['below'] + margin){
	            path[choice_point][0] = tgt['height'];
	        }

        } else {
	        if (
	            (tgt['rad'] < point_bounds['radmax']   - margin) &&
	            (tgt['rad'] > point_bounds['radmin']   + margin) &&
	            (tgt['height'] < point_bounds['above'] - margin) &&
	            (tgt['height'] > point_bounds['below'] + margin) )
	        {
	            path[choice_point][1] = tgt['rad'];
	            path[choice_point][0] = tgt['height'];
	        }
        }
    }
}

function fco_to_cvco(rad,height){
    return {
        'x': 390+rad*zoom,
        'y': 800-height*zoom
    };
}

function cvco_to_fco(cx,cy){
    return {
        'rad': (cx-390)/zoom,
        'height': (800-cy)/zoom
    };
}

function labelVertGuide(ctx, rad, str){
    ctx.strokeStyle = "rgb(250,250,250)";
    ctx.font = 'italic 12px Calibri';
    ctx.fillStyle = "rgb(220,220,200)";
    ctx.beginPath();
    ptg = fco_to_cvco(rad,0)
    x = ptg.x + 0.5
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 800);
    ctx.stroke();
    ctx.fillText(str, x+1.5, 10);
}

function labelHoriGuide(ctx, hi, str){
    ctx.strokeStyle = "rgb(250,250,250)";
    ctx.font = 'italic 12px Calibri';
    ctx.fillStyle = "rgb(220,220,200)";
    ctx.beginPath();
    ptg = fco_to_cvco(0,hi)
    y = ptg.y + 0.5
    ctx.moveTo(0, y);
    ctx.lineTo(800, y);
    ctx.stroke();
    ctx.fillText(str, 800-19.5, y+10);
}
        
function draw(mouseX,mouseY){
    var canvas = document.getElementById("usp");
    if (canvas.getContext){
        var ctx = canvas.getContext("2d");

        // width: 800, height: 800

        ctx.fillStyle = "rgb(180,180,180)";
        ctx.fillRect (0, 0, 800, 800);
        
	if (showPicture){
	    var img_nw = 224 * (zoom/80);
	    // native 224 201
	    // zoom is conveniently in units of pixels per meter
	    // this image is 80 pixels per meter
	    ctx.drawImage(refimage, 390-(img_nw/2), 800-(281*(zoom/80)), img_nw, img_nw * refimage.height / refimage.width);
	}

	if (showMeasures){
	    // light 1m 2m 3m lines
	    labelVertGuide(ctx, 0, '0m');
	    for (var meters=1; meters<60; meters++){
        	labelVertGuide(ctx, -meters, meters+'m');
        	labelVertGuide(ctx, meters, meters+'m');
		labelHoriGuide(ctx, meters, meters+'m')
	    }
	}

        // fairing profile line segments
        for (var mu=1; mu>=-1; mu-=2){
            ctx.beginPath();
            ctx.strokeStyle = "rgb(0,0,0)";
            for(var i=0; i<path.length; i++){
                var np = path[i];
                var cvco = fco_to_cvco(mu*np[1], np[0]);
                if (i==0){
                    ctx.moveTo(cvco.x, cvco.y);
                } else {
                    ctx.lineTo(cvco.x, cvco.y);
                }
            }
            ctx.stroke();
        }

        if (choice_point != -1){
            cp = path[choice_point];
            co = fco_to_cvco(choice_side*cp[1], cp[0]);
            ctx.beginPath();
            ctx.arc(co.x, co.y, 4, 0, 2 * Math.PI, false);
            ctx.strokeStyle = "rgb(0, 0, 0)";
            ctx.stroke();
        }

	// orange section
	ctx.fillStyle = "rgb(212,95,0)";
        ctx.fillRect (0, 0, 20, 800);
        ctx.strokeStyle = "rgb(0,0,0)";
        ctx.beginPath();
        ctx.moveTo(20, 0);
        ctx.lineTo(20, 800);
        ctx.stroke();


        // existing cuts
        for(var i=0; i<cuts.length-1; i++){
            var cvco = fco_to_cvco(0, cuts[i]);
            // plain clor
            ctx.strokeStyle = "rgb(200,45,0)";
            // if not first or last cut (special)
            if (i == choice_cut){
                ctx.strokeStyle = "rgb(255,255,0)";
            }
            ctx.beginPath();
            ctx.moveTo(0, cvco.y);
            ctx.lineTo(800, cvco.y);
            ctx.stroke();
        }

        
        if (candidate_point){
            cgan = fco_to_cvco( candidate_point['rad'], candidate_point['height'] );
            // mouse dot
            ctx.beginPath();
            ctx.arc(cgan.x, cgan.y, 4, 0, 2 * Math.PI, false);
            ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
            ctx.fill();
            // other side
            var fairing_co = cvco_to_fco(cgan.x, cgan.y);
            var canvas_co = fco_to_cvco(-1*fairing_co.rad, fairing_co.height);
            ctx.beginPath();
            ctx.arc(canvas_co.x, canvas_co.y, 4, 0, 2 * Math.PI, false);
            ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
            ctx.fill();
        }

        if (candidate_cut){
            cgan = fco_to_cvco(0,candidate_cut['height']);
            ctx.strokeStyle = "rgb(100,0,0)";
            ctx.beginPath();
            ctx.moveTo(0, cgan.y);
            ctx.lineTo(20, cgan.y);
            ctx.stroke();
        }
    }
}