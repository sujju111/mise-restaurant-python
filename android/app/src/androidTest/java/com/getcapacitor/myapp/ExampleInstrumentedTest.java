package com.getcapacitor.myapp;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import android.webkit.WebView;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.mise.restaurant.MainActivity;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;
@RunWith(AndroidJUnit4.class)
public class ExampleInstrumentedTest {
 @Test public void rustWorkspaceBootsOnDevice() throws Exception {
  try(ActivityScenario<MainActivity> scenario=ActivityScenario.launch(MainActivity.class)){
   AtomicReference<String> result=new AtomicReference<>("false");
   long deadline=System.currentTimeMillis()+30000;
   do{
    CountDownLatch callback=new CountDownLatch(1);
    scenario.onActivity(activity->{WebView web=activity.getBridge().getWebView();web.evaluateJavascript("Boolean(document.querySelector('nav[aria-label=\"Main navigation\"]') && document.body.innerText.includes('Juniper House') && document.body.innerText.includes('Rust engine'))",value->{result.set(value);callback.countDown();});});
    assertTrue("WebView callback timed out",callback.await(5,TimeUnit.SECONDS));
    if("true".equals(result.get()))break;
    Thread.sleep(250);
   }while(System.currentTimeMillis()<deadline);
   assertEquals("Vue + Rust WASM workspace must render","true",result.get());
  }
 }
}
