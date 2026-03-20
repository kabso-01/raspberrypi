using UnityEngine;
using System;
using System.Collections;

public class BLEManager : MonoBehaviour
{
    private const string SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
    private const string CHAR_UUID    = "12345678-1234-1234-1234-123456789def";
    private const string DEVICE_NAME  = "HrrmonieRadar";

    public static BLEManager Instance { get; private set; }
    public float  HeartRate           { get; private set; } = 0f;
    public float  RespRate            { get; private set; } = 0f;
    public bool   IsConnected         { get; private set; } = false;
    public string StatusMessage       { get; private set; } = "Initialisation...";

    private AndroidJavaObject _bluetoothAdapter;
    private AndroidJavaObject _bluetoothGatt;
    private BLECallback       _gattCallback;
    private ScanCallback      _scanCallback;
    private AndroidJavaObject _leScanner;
    private bool              _scanning = false;

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        StartCoroutine(InitBLE());
#else
        Debug.Log("[BLE] Mode Editor — simulation activée");
        StatusMessage = "Simulation (Editor)";
        InvokeRepeating(nameof(SimulateData), 2f, 1f);
#endif
    }

    void Update()
    {
        MainThreadDispatcher.Update();
    }

    IEnumerator InitBLE()
    {
        yield return RequestBLEPermissions();
        try
        {
            using var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
            using var activity    = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");
            using var context     = activity.Call<AndroidJavaObject>("getApplicationContext");
            using var btManager   = context.Call<AndroidJavaObject>("getSystemService", "bluetooth");
            _bluetoothAdapter     = btManager.Call<AndroidJavaObject>("getAdapter");

            if (_bluetoothAdapter == null)
            { StatusMessage = "Bluetooth non disponible"; yield break; }

            if (!_bluetoothAdapter.Call<bool>("isEnabled"))
            { StatusMessage = "Activez le Bluetooth du Quest"; yield break; }

            StatusMessage = "Scan en cours...";
            StartCoroutine(ScanForDevice());
        }
        catch (Exception e)
        {
            StatusMessage = "Erreur init BLE";
            Debug.LogError("[BLE] Init : " + e.Message);
        }
    }

    IEnumerator RequestBLEPermissions()
    {
#if UNITY_ANDROID
        if (!UnityEngine.Android.Permission.HasUserAuthorizedPermission("android.permission.BLUETOOTH_SCAN"))
        {
            UnityEngine.Android.Permission.RequestUserPermission("android.permission.BLUETOOTH_SCAN");
            yield return new WaitForSeconds(1f);
        }
        if (!UnityEngine.Android.Permission.HasUserAuthorizedPermission("android.permission.BLUETOOTH_CONNECT"))
        {
            UnityEngine.Android.Permission.RequestUserPermission("android.permission.BLUETOOTH_CONNECT");
            yield return new WaitForSeconds(1f);
        }
#endif
        yield return null;
    }

    IEnumerator ScanForDevice()
    {
        if (_scanning) yield break;
        _scanning = true;

        try
        {
            _leScanner    = _bluetoothAdapter.Call<AndroidJavaObject>("getBluetoothLeScanner");
            _scanCallback = new ScanCallback(OnDeviceFound);
            _leScanner.Call("startScan", _scanCallback);
            StatusMessage = "Scan BLE démarré...";
            Debug.Log("[BLE] Scan démarré");
        }
        catch (Exception e)
        {
            Debug.LogError("[BLE] Scan : " + e.Message);
            _scanning = false;
            yield break;
        }

        yield return new WaitForSeconds(15f);

        if (!IsConnected)
        {
            try { _leScanner?.Call("stopScan", _scanCallback); } catch { }
            StatusMessage = "Appareil non trouvé — relance...";
            _scanning = false;
            StartCoroutine(ScanForDevice());
        }
    }

    void OnDeviceFound(AndroidJavaObject device)
    {
        try
        {
            string name = device.Call<string>("getName");
            if (string.IsNullOrEmpty(name) || !name.Contains(DEVICE_NAME)) return;

            Debug.Log("[BLE] Cible trouvée : " + name);
            try { _leScanner?.Call("stopScan", _scanCallback); } catch { }

            MainThreadDispatcher.Enqueue(() => ConnectToDevice(device));
        }
        catch (Exception e) { Debug.LogError("[BLE] OnDeviceFound : " + e.Message); }
    }

    void ConnectToDevice(AndroidJavaObject device)
    {
        try
        {
            using var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
            using var activity    = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");

            _gattCallback = new BLECallback(
                onConnected:    OnGattConnected,
                onDisconnected: OnGattDisconnected,
                onDataReceived: ParseData
            );
            _bluetoothGatt = device.Call<AndroidJavaObject>("connectGatt", activity, false, _gattCallback);
            StatusMessage  = "Connexion GATT...";
        }
        catch (Exception e) { Debug.LogError("[BLE] ConnectToDevice : " + e.Message); }
    }

    void OnGattConnected()
    {
        IsConnected   = true;
        StatusMessage = "Connecté à HrrmonieRadar";
        Debug.Log("[BLE] Connecté — découverte services...");
        _bluetoothGatt?.Call("discoverServices");
    }

    void OnGattDisconnected()
    {
        IsConnected   = false;
        StatusMessage = "Déconnecté — relance scan...";
        _scanning     = false;
        StartCoroutine(ScanForDevice());
    }

    void ParseData(byte[] bytes)
    {
        try
        {
            string json    = System.Text.Encoding.UTF8.GetString(bytes);
            VitalData data = JsonUtility.FromJson<VitalData>(json);
            HeartRate      = data.hr;
            RespRate       = data.rr;
            Debug.Log($"[BLE] HR={data.hr} | RR={data.rr}");
        }
        catch (Exception e) { Debug.LogError("[BLE] ParseData : " + e.Message); }
    }

    void SimulateData()
    {
        HeartRate     = Mathf.Round(UnityEngine.Random.Range(65f, 80f) * 10f) / 10f;
        RespRate      = Mathf.Round(UnityEngine.Random.Range(14f, 20f) * 10f) / 10f;
        IsConnected   = true;
        StatusMessage = "Simulation active";
    }

    void OnDestroy()
    {
        try { _bluetoothGatt?.Call("disconnect"); _bluetoothGatt?.Call("close"); } catch { }
    }
}

// ─── Callback GATT ───────────────────────────────────────
public class BLECallback : AndroidJavaProxy
{
    private readonly Action         _onConnected;
    private readonly Action         _onDisconnected;
    private readonly Action<byte[]> _onDataReceived;

    public BLECallback(Action onConnected, Action onDisconnected, Action<byte[]> onDataReceived)
        : base("android.bluetooth.BluetoothGattCallback")
    {
        _onConnected    = onConnected;
        _onDisconnected = onDisconnected;
        _onDataReceived = onDataReceived;
    }

    public void onConnectionStateChange(AndroidJavaObject gatt, int status, int newState)
    {
        if (newState == 2)      MainThreadDispatcher.Enqueue(_onConnected);
        else if (newState == 0) MainThreadDispatcher.Enqueue(_onDisconnected);
    }

    public void onServicesDiscovered(AndroidJavaObject gatt, int status)
    {
        MainThreadDispatcher.Enqueue(() =>
        {
            try
            {
                using var uuidClass  = new AndroidJavaClass("java.util.UUID");
                var svcUUID  = uuidClass.CallStatic<AndroidJavaObject>("fromString", "12345678-1234-1234-1234-123456789abc");
                var chrUUID  = uuidClass.CallStatic<AndroidJavaObject>("fromString", "12345678-1234-1234-1234-123456789def");
                var service  = gatt.Call<AndroidJavaObject>("getService", svcUUID);
                if (service == null) { Debug.LogError("[BLE] Service introuvable"); return; }
                var chr = service.Call<AndroidJavaObject>("getCharacteristic", chrUUID);
                if (chr == null) { Debug.LogError("[BLE] Caractéristique introuvable"); return; }

                gatt.Call<bool>("setCharacteristicNotification", chr, true);

                var descUUID = uuidClass.CallStatic<AndroidJavaObject>("fromString", "00002902-0000-1000-8000-00805f9b34fb");
                var desc     = chr.Call<AndroidJavaObject>("getDescriptor", descUUID);
                if (desc != null)
                {
                    using var descClass = new AndroidJavaClass("android.bluetooth.BluetoothGattDescriptor");
                    desc.Call<bool>("setValue", descClass.GetStatic<byte[]>("ENABLE_NOTIFICATION_VALUE"));
                    gatt.Call<bool>("writeDescriptor", desc);
                }
                Debug.Log("[BLE] Notifications activées");
            }
            catch (Exception e) { Debug.LogError("[BLE] onServicesDiscovered : " + e.Message); }
        });
    }

    public void onCharacteristicChanged(AndroidJavaObject gatt, AndroidJavaObject characteristic)
    {
        try
        {
            byte[] value = characteristic.Call<byte[]>("getValue");
            MainThreadDispatcher.Enqueue(() => _onDataReceived?.Invoke(value));
        }
        catch (Exception e) { Debug.LogError("[BLE] onCharacteristicChanged : " + e.Message); }
    }
}

// ─── Callback Scan ───────────────────────────────────────
public class ScanCallback : AndroidJavaProxy
{
    private readonly Action<AndroidJavaObject> _onDeviceFound;

    public ScanCallback(Action<AndroidJavaObject> onDeviceFound)
        : base("android.bluetooth.le.ScanCallback")
    {
        _onDeviceFound = onDeviceFound;
    }

    public void onScanResult(int callbackType, AndroidJavaObject result)
    {
        _onDeviceFound?.Invoke(result.Call<AndroidJavaObject>("getDevice"));
    }
}

// ─── MainThreadDispatcher ────────────────────────────────
public static class MainThreadDispatcher
{
    private static readonly System.Collections.Generic.Queue<Action> _queue = new();
    private static readonly object _lock = new();

    public static void Enqueue(Action action)
    {
        lock (_lock) { _queue.Enqueue(action); }
    }

    public static void Update()
    {
        lock (_lock)
        {
            while (_queue.Count > 0) _queue.Dequeue()?.Invoke();
        }
    }
}

// ─── Modèle JSON ─────────────────────────────────────────
[Serializable]
public class VitalData
{
    public float hr;
    public float rr;
}
