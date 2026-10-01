import java.util.HashMap;
import java.util.Map;
import java.util.prefs.AbstractPreferences;
import java.util.prefs.Preferences;
import java.util.prefs.PreferencesFactory;

/** Keeps integration tests from reading or changing the user's Java preferences. */
public class MemoryPreferencesFactory implements PreferencesFactory {
    private final Preferences user = new MemoryPreferences(null, "");
    private final Preferences system = new MemoryPreferences(null, "");
    public Preferences userRoot() { return user; }
    public Preferences systemRoot() { return system; }

    private static class MemoryPreferences extends AbstractPreferences {
        private final Map<String, String> values = new HashMap<>();
        private final Map<String, MemoryPreferences> children = new HashMap<>();
        MemoryPreferences(AbstractPreferences parent, String name) { super(parent, name); }
        protected void putSpi(String key, String value) { values.put(key, value); }
        protected String getSpi(String key) { return values.get(key); }
        protected void removeSpi(String key) { values.remove(key); }
        protected void removeNodeSpi() { values.clear(); children.clear(); }
        protected String[] keysSpi() { return values.keySet().toArray(new String[0]); }
        protected String[] childrenNamesSpi() { return children.keySet().toArray(new String[0]); }
        protected AbstractPreferences childSpi(String name) {
            return children.computeIfAbsent(name, n -> new MemoryPreferences(this, n));
        }
        protected void syncSpi() {}
        protected void flushSpi() {}
    }
}
