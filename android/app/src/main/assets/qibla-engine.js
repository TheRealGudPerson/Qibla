/* Qibla's shared, dependency-free calculation engine. Used by web and Android WebView. */
(() => {
  'use strict';
  const KAABA = Object.freeze({ lat: 21.422487, lon: 39.826206 });
  const EARTH_KM = 6371.0088;
  const norm = d => ((d % 360) + 360) % 360;
  const rad = d => d * Math.PI / 180;
  const deg = r => r * 180 / Math.PI;
  function validate(lat, lon) {
    if (!Number.isFinite(lat) || lat < -90 || lat > 90) throw new RangeError('Latitude must be between -90 and 90.');
    if (!Number.isFinite(lon) || lon < -180 || lon > 180) throw new RangeError('Longitude must be between -180 and 180.');
  }
  function bearing(lat, lon) {
    validate(lat, lon);
    const p=rad(lat), k=rad(KAABA.lat), dl=rad(KAABA.lon-lon);
    return norm(deg(Math.atan2(Math.sin(dl)*Math.cos(k), Math.cos(p)*Math.sin(k)-Math.sin(p)*Math.cos(k)*Math.cos(dl))));
  }
  function distance(lat, lon) {
    validate(lat, lon);
    const p=rad(lat), k=rad(KAABA.lat), dl=rad(KAABA.lon-lon), dp=k-p;
    const a=Math.min(1,Math.max(0,Math.sin(dp/2)**2+Math.cos(p)*Math.cos(k)*Math.sin(dl/2)**2));
    return 2*EARTH_KM*Math.asin(Math.sqrt(a));
  }
  function direction(d) { return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'][Math.round(norm(d)/22.5)%16]; }
  function destination(lat, lon, brg, km) {
    validate(lat,lon); const a=km/EARTH_KM,b=rad(brg),p=rad(lat),l=rad(lon);
    const p2=Math.asin(Math.sin(p)*Math.cos(a)+Math.cos(p)*Math.sin(a)*Math.cos(b));
    const l2=l+Math.atan2(Math.sin(b)*Math.sin(a)*Math.cos(p),Math.cos(a)-Math.sin(p)*Math.sin(p2));
    return {lat:deg(p2),lon:((deg(l2)+540)%360)-180};
  }
  function solar(lat, lon, date=new Date()) {
    validate(lat,lon);
    const day=Math.floor((Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate())-Date.UTC(date.getUTCFullYear(),0,0))/86400000);
    const hour=date.getUTCHours()+date.getUTCMinutes()/60+date.getUTCSeconds()/3600;
    const g=2*Math.PI/365*(day-1+(hour-12)/24);
    const eq=229.18*(.000075+.001868*Math.cos(g)-.032077*Math.sin(g)-.014615*Math.cos(2*g)-.040849*Math.sin(2*g));
    const dec=.006918-.399912*Math.cos(g)+.070257*Math.sin(g)-.006758*Math.cos(2*g)+.000907*Math.sin(2*g)-.002697*Math.cos(3*g)+.00148*Math.sin(3*g);
    const mins=((hour*60+eq+4*lon)%1440+1440)%1440, ha=mins/4-180, h=rad(ha), p=rad(lat);
    const cz=Math.min(1,Math.max(-1,Math.sin(p)*Math.sin(dec)+Math.cos(p)*Math.cos(dec)*Math.cos(h)));
    const elevation=90-deg(Math.acos(cz));
    const azimuth=norm(deg(Math.atan2(Math.sin(h),Math.cos(h)*Math.sin(p)-Math.tan(dec)*Math.cos(p)))+180);
    return {azimuth,elevation,isDaylight:elevation>0,declination:deg(dec),equationOfTime:eq};
  }
  const METHODS = Object.freeze({
    MWL:{label:'Muslim World League',fajr:18,isha:17},
    ISNA:{label:'ISNA',fajr:15,isha:15},
    EGYPT:{label:'Egyptian General Authority',fajr:19.5,isha:17.5},
    MAKKAH:{label:'Umm al-Qura (Makkah)',fajr:18.5,isha:null,ishaMinutes:90},
    KARACHI:{label:'University of Islamic Sciences, Karachi',fajr:18,isha:18},
    TEHRAN:{label:'Institute of Geophysics, Tehran',fajr:17.7,isha:14},
    SINGAPORE:{label:'MUIS Singapore',fajr:20,isha:18},
  });
  function solarDeclinationAndEot(date) {
    const day=Math.floor((Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate())-Date.UTC(date.getUTCFullYear(),0,0))/86400000);
    const hour=date.getUTCHours()+date.getUTCMinutes()/60;
    const g=2*Math.PI/365*(day-1+(hour-12)/24);
    const eq=229.18*(.000075+.001868*Math.cos(g)-.032077*Math.sin(g)-.014615*Math.cos(2*g)-.040849*Math.sin(2*g));
    const dec=.006918-.399912*Math.cos(g)+.070257*Math.sin(g)-.006758*Math.cos(2*g)+.000907*Math.sin(2*g)-.002697*Math.cos(3*g)+.00148*Math.sin(3*g);
    return {dec,eq};
  }
  function prayerTimes(lat, lon, date=new Date(), options={}) {
    validate(lat,lon);
    const method=METHODS[options.method||'MWL'] || METHODS.MWL;
    const asrFactor=options.asr==='hanafi'?2:1;
    const offset=Number.isFinite(options.utcOffsetMinutes)?options.utcOffsetMinutes:-date.getTimezoneOffset();
    const localNoonDate=new Date(Date.UTC(date.getFullYear(),date.getMonth(),date.getDate(),12)-offset*60000);
    const {dec,eq}=solarDeclinationAndEot(localNoonDate);
    const phi=rad(lat);
    const noon=12+offset/60-lon/15-eq/60;
    function hourAngle(altitudeDeg) {
      const alt=rad(altitudeDeg), c=(Math.sin(alt)-Math.sin(phi)*Math.sin(dec))/(Math.cos(phi)*Math.cos(dec));
      if(c < -1 || c > 1) return null;
      return deg(Math.acos(c))/15;
    }
    const sunriseAngle=hourAngle(-0.833);
    let fajrAngle=hourAngle(-method.fajr);
    let ishaAngle=method.isha===null?null:hourAngle(-method.isha);
    const sunsetAngle=sunriseAngle;
    if(sunriseAngle===null) return {date: `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`,method:method.label,asr:options.asr==='hanafi'?'Hanafi':'Standard',times:{},unavailable:true,message:'Sunrise/sunset cannot be estimated at this latitude for this date.'};
    if(fajrAngle===null) fajrAngle=sunriseAngle*Math.min(1,method.fajr/60);
    if(ishaAngle===null && method.isha!==null) ishaAngle=sunriseAngle*Math.min(1,method.isha/60);
    const sunrise=noon-sunriseAngle, sunset=noon+sunsetAngle;
    const asrAltitude=deg(Math.atan(1/(asrFactor+Math.tan(Math.abs(phi-dec)))));
    let asrAngle=hourAngle(asrAltitude); if(asrAngle===null) asrAngle=sunriseAngle*.5;
    const raw={Fajr:noon-(fajrAngle??sunriseAngle*.5),Sunrise:sunrise,Dhuhr:noon+1/60,Asr:noon+asrAngle,Maghrib:sunset,Isha:method.ishaMinutes!=null? sunset+method.ishaMinutes/60 : noon+(ishaAngle??sunriseAngle*.5)};
    const fmt=v=>{v=((v%24)+24)%24;const h=Math.floor(v),m=Math.floor((v-h)*60+0.5);const hh=(h+(m===60?1:0))%24;return `${String(hh).padStart(2,'0')}:${String(m===60?0:m).padStart(2,'0')}`;};
    const times={};for(const [k,v] of Object.entries(raw)) times[k]=fmt(v);
    return {date:`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`,method:method.label,methodId:options.method||'MWL',asr:options.asr==='hanafi'?'Hanafi':'Standard',times,unavailable:false};
  }
  const api={KAABA,METHODS,norm,validate,bearing,distance,direction,destination,solar,prayerTimes};
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(typeof window!=='undefined') window.QiblaEngine=api;
})();
