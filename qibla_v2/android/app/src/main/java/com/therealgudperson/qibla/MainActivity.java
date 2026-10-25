package com.therealgudperson.qibla;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.hardware.GeomagneticField;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.core.app.ActivityCompat;
import android.content.Context;
import java.util.Locale;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import org.json.JSONArray;
import org.json.JSONObject;

public class MainActivity extends Activity implements SensorEventListener {
    private static final int LOCATION_PERMISSION = 41;
    private WebView webView;
    private SensorManager sensorManager;
    private Sensor rotationSensor;
    private LocationManager locationManager;
    private volatile float magneticAzimuth = Float.NaN;
    private volatile Location lastLocation;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(android.graphics.Color.rgb(16,39,31));
        getWindow().setNavigationBarColor(android.graphics.Color.rgb(9,21,16));
        sensorManager = (SensorManager)getSystemService(Context.SENSOR_SERVICE);
        rotationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
        locationManager = (LocationManager)getSystemService(Context.LOCATION_SERVICE);

        webView = new WebView(this);
        setContentView(webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                if (hasLocationPermission()) callback.invoke(origin, true, false);
                else {
                    ActivityCompat.requestPermissions(MainActivity.this,
                        new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION},
                        LOCATION_PERMISSION);
                    callback.invoke(origin, false, false);
                }
            }
        });
        webView.addJavascriptInterface(new QiblaBridge(), "QiblaNative");
        webView.loadUrl("file:///android_asset/index.html");
        if (!hasLocationPermission()) {
            ActivityCompat.requestPermissions(this,
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION},
                LOCATION_PERMISSION);
        } else {
            refreshLastLocation();
        }
    }

    private boolean hasLocationPermission() {
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            || ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void refreshLastLocation() {
        if (!hasLocationPermission()) return;
        try {
            Location gps = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            Location network = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            if (gps != null) lastLocation = gps;
            if (network != null && (lastLocation == null || network.getTime() > lastLocation.getTime())) lastLocation = network;
            String provider = locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) ? LocationManager.GPS_PROVIDER : LocationManager.NETWORK_PROVIDER;
            locationManager.requestLocationUpdates(provider, 1000L, 0f, new LocationListener() {
                @Override public void onLocationChanged(Location location) { lastLocation = location; }
                @Override public void onProviderEnabled(String provider) {}
                @Override public void onProviderDisabled(String provider) {}
                @Override public void onStatusChanged(String provider, int status, Bundle extras) {}
            });
        } catch (SecurityException ignored) {}
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_PERMISSION && hasLocationPermission()) refreshLastLocation();
    }

    @Override protected void onResume() {
        super.onResume();
        if (rotationSensor != null) sensorManager.registerListener(this, rotationSensor, SensorManager.SENSOR_DELAY_UI);
        if (hasLocationPermission()) refreshLastLocation();
    }

    @Override protected void onPause() {
        super.onPause();
        sensorManager.unregisterListener(this);
    }

    @Override public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() != Sensor.TYPE_ROTATION_VECTOR) return;
        float[] matrix = new float[9];
        float[] orientation = new float[3];
        SensorManager.getRotationMatrixFromVector(matrix, event.values);
        SensorManager.getOrientation(matrix, orientation);
        magneticAzimuth = (float)((Math.toDegrees(orientation[0]) + 360.0) % 360.0);
    }

    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    private class QiblaBridge {
        @JavascriptInterface public String getTrueHeading(String latitude, String longitude) {
            float magnetic = magneticAzimuth;
            if (Float.isNaN(magnetic)) return "";
            try {
                float lat = Float.parseFloat(latitude), lon = Float.parseFloat(longitude);
                float altitude = lastLocation == null ? 0f : (float)lastLocation.getAltitude();
                GeomagneticField field = new GeomagneticField(lat, lon, altitude, System.currentTimeMillis());
                return String.format(Locale.US, "%.3f", (magnetic + field.getDeclination() + 360f) % 360f);
            } catch (Exception e) { return ""; }
        }

        @JavascriptInterface public String getLocationJson() {
            if (!hasLocationPermission()) return "";
            refreshLastLocation();
            Location location = lastLocation;
            if (location == null) return "";
            return String.format(Locale.US,
                "{\"latitude\":%.7f,\"longitude\":%.7f,\"accuracy\":%.1f,\"name\":\"Current device location\"}",
                location.getLatitude(), location.getLongitude(), location.getAccuracy());
        }

        @JavascriptInterface public String searchPlace(String query) {
            HttpURLConnection connection = null;
            try {
                String encoded = URLEncoder.encode(query, "UTF-8");
                URL url = new URL("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=" + encoded);
                connection = (HttpURLConnection)url.openConnection();
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(15000);
                connection.setRequestProperty("User-Agent", "Qibla/2.0 (personal use)");
                connection.setRequestProperty("Accept-Language", "en");
                StringBuilder body = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), "UTF-8"))) {
                    String line;
                    while ((line = reader.readLine()) != null) body.append(line);
                }
                JSONArray results = new JSONArray(body.toString());
                if (results.length() == 0) return "{\\"error\\":\\"Place not found. Add a state or country.\\"}";
                JSONObject item = results.getJSONObject(0);
                JSONObject result = new JSONObject();
                result.put("latitude", Double.parseDouble(item.getString("lat")));
                result.put("longitude", Double.parseDouble(item.getString("lon")));
                result.put("name", item.optString("display_name", query));
                return result.toString();
            } catch (Exception e) {
                return "{\\"error\\":\\"City lookup failed. Check internet and try again.\\"}";
            } finally {
                if (connection != null) connection.disconnect();
            }
        }

        @JavascriptInterface public boolean hasRotationSensor() { return rotationSensor != null; }
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
