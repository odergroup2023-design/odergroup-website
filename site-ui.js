/* Başlık ve erişilebilir etkileşimler; dış servis/analitik ayarları değişmez. */
(function(){
 'use strict';
 var nav=document.querySelector('header.nav .wrap'), lang=document.getElementById('langbox'), strip=document.querySelector('.strip .r');
 var burger=document.getElementById('burger'),menu=document.getElementById('menu'),langbtn=document.getElementById('langbtn');
 var compact=window.matchMedia('(max-width:1080px)');
 function moveLanguage(){
  if(nav&&lang){if(compact.matches)nav.insertBefore(lang,burger);else if(strip)strip.appendChild(lang);}
  if(menu)menu.inert=compact.matches&&!menu.classList.contains('open');
 }
 moveLanguage();compact.addEventListener('change',moveLanguage);
 function sync(){
  if(menu&&burger){var open=menu.classList.contains('open');burger.setAttribute('aria-expanded',String(open));menu.inert=compact.matches&&!open;}
  if(lang&&langbtn){langbtn.setAttribute('aria-expanded',String(lang.classList.contains('open')));var code=document.getElementById('langkod');langbtn.setAttribute('aria-label',(code?code.textContent:'TR')+' — Dil seçimi / Language');}
 }
 if(menu)new MutationObserver(sync).observe(menu,{attributes:true,attributeFilter:['class']});
 if(lang)new MutationObserver(sync).observe(lang,{attributes:true,attributeFilter:['class']});
 if(langbtn)new MutationObserver(sync).observe(langbtn,{childList:true,subtree:true});
 document.addEventListener('keydown',function(e){
  if(e.key==='Escape'){
   if(lang&&lang.classList.contains('open')){lang.classList.remove('open');langbtn.focus();}
   else if(menu&&menu.classList.contains('open')){menu.classList.remove('open');burger.focus();}
  }
 });
 document.addEventListener('click',function(e){
  if(menu&&compact.matches&&!e.target.closest('header.nav'))menu.classList.remove('open');
 });
 if(langbtn)langbtn.addEventListener('click',function(){
  if(menu)menu.classList.remove('open');
  if(lang.classList.contains('open')){var option=lang.querySelector('.langmenu button');if(option)option.focus();}
 });
 if(burger)burger.addEventListener('click',function(){
  if(lang)lang.classList.remove('open');
  if(menu&&menu.classList.contains('open')){menu.inert=false;var first=menu.querySelector('a');if(first)first.focus();}
 });
 document.querySelectorAll('.fq').forEach(function(fq,index){
  var button=fq.querySelector('button'),answer=fq.querySelector('.a,.ans');if(!button||!answer)return;
  answer.id=answer.id||'faq-answer-'+index;button.setAttribute('aria-controls',answer.id);
  function update(){button.setAttribute('aria-expanded',String(fq.classList.contains('open')));}
  update();new MutationObserver(update).observe(fq,{attributes:true,attributeFilter:['class']});
 });
 // Galeri görselleri klavye ile de açılır. Mevcut tıklama işlevi korunur.
 document.querySelectorAll('.gi').forEach(function(figure){
  figure.tabIndex=0;figure.setAttribute('role','button');
  var im=figure.querySelector('img');figure.setAttribute('aria-label',(im?im.alt:'Görsel')+' — büyüt');
  figure.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();figure.click();}});
 });
 sync();
})();
