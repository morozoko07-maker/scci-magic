/* Dithered shader panels. Progressive: without WebGL the img/CSS fallback stays. */
(function () {
  "use strict";
  if (!("WebGLRenderingContext" in window)) return;

  var VS = "attribute vec2 p;varying vec2 v;void main(){v=p*0.5+0.5;gl_Position=vec4(p,0.0,1.0);}";
  var FS = [
    "precision mediump float;",
    "varying vec2 v;",
    "uniform sampler2D tex;uniform float has,time,hover,seed;",
    "uniform vec2 res;uniform vec3 accent;",
    "float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}",
    "void main(){",
    "  vec2 uv=v;",
    "  uv.x += sin(uv.y*38.0+time*1.3)*0.004*(1.0+hover*3.0);",
    "  vec3 col;",
    "  if(has>0.5){col=texture2D(tex,uv).rgb;}",
    "  else{float n=hash(floor(uv*vec2(64.0,36.0))+seed+floor(time*0.6));col=mix(vec3(0.03),accent,n*0.85);}",
    "  float lum=dot(col,vec3(0.299,0.587,0.114));",
    "  vec2 cell=floor(v*res/3.0);float b=mod(cell.x+cell.y*4.0,16.0)/16.0;",
    "  float d=step(b,lum*0.95+0.03);",
    "  vec3 outv=mix(vec3(0.02),accent*1.15,d);",
    "  outv*=0.88+0.12*sin(v.y*res.y*1.7);",
    "  outv*=1.0-0.30*length(v-0.5);",
    "  gl_FragColor=vec4(outv,1.0);",
    "}"
  ].join("\n");

  function compile(gl, type, src) {
    var sh = gl.createShader(type);
    gl.shaderSource(sh, src); gl.compileShader(sh);
    return gl.getShaderParameter(sh, gl.COMPILE_STATUS) ? sh : null;
  }

  function hexToRgb(hex) {
    var m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex || "");
    return m ? [parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255] : [0.56, 0.65, 0.56];
  }

  function mount(canvas) {
    var gl = canvas.getContext("webgl", { antialias: false, alpha: false });
    if (!gl) return;
    var vsh = compile(gl, gl.VERTEX_SHADER, VS);
    var fsh = compile(gl, gl.FRAGMENT_SHADER, FS);
    if (!vsh || !fsh) return;
    var prog = gl.createProgram();
    gl.attachShader(prog, vsh); gl.attachShader(prog, fsh); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);

    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    var u = {
      tex: gl.getUniformLocation(prog, "tex"), has: gl.getUniformLocation(prog, "has"),
      time: gl.getUniformLocation(prog, "time"), hover: gl.getUniformLocation(prog, "hover"),
      seed: gl.getUniformLocation(prog, "seed"), res: gl.getUniformLocation(prog, "res"),
      accent: gl.getUniformLocation(prog, "accent")
    };
    var accent = hexToRgb(canvas.getAttribute("data-accent"));
    var seed = (parseInt(canvas.getAttribute("data-seed") || "1", 10) % 97) / 7;
    gl.uniform3f(u.accent, accent[0], accent[1], accent[2]);
    gl.uniform1f(u.seed, seed);
    gl.uniform1f(u.has, 0);

    var src = canvas.getAttribute("data-src");
    if (src) {
      var img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = function () {
        var tex = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.uniform1i(u.tex, 0);
        gl.uniform1f(u.has, 1);
      };
      img.src = src;
    }

    var hover = 0, target = 0, running = false, raf = 0, t0 = performance.now();
    canvas.addEventListener("pointerenter", function () { target = 1; });
    canvas.addEventListener("pointerleave", function () { target = 0; });

    function size() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var w = canvas.clientWidth || 600, h = canvas.clientHeight || 380;
      if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
        canvas.width = Math.floor(w * dpr); canvas.height = Math.floor(h * dpr);
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
      gl.uniform2f(u.res, canvas.width, canvas.height);
    }

    function frame(now) {
      size();
      hover += (target - hover) * 0.08;
      gl.uniform1f(u.time, (now - t0) / 1000);
      gl.uniform1f(u.hover, hover);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      if (running) raf = requestAnimationFrame(frame);
    }

    function start() { if (running) return; running = true; raf = requestAnimationFrame(frame); }
    function stop() { running = false; cancelAnimationFrame(raf); }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      frame(performance.now());
      return;
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { e.isIntersecting ? start() : stop(); });
      }, { threshold: 0.05 }).observe(canvas);
    } else { start(); }
    window.addEventListener("resize", size);
  }

  var panels = document.querySelectorAll("canvas[data-shader]");
  for (var i = 0; i < panels.length; i++) {
    try { mount(panels[i]); } catch (e) { /* keep CSS fallback */ }
  }
})();
