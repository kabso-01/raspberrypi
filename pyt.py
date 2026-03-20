using UnityEngine;
using System;

public class BLEManager : MonoBehaviour
{
    // =====================================================
    // UUIDs — identiques à ble_server_radar.py sur la Raspi
    // =====================================================
    public static readonly string SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
    public static readonly string CHAR_UUID    = "12345678-1234-1234-1234-123456789def";
    public static readonly string DEVICE_NAME  = "HrrmonieRadar";

    // =====================================================
    // Données accessibles depuis les autres scripts
    // =====================================================
    public float HeartRate   { get; private set; } = 0f;
    public float RespRate    { get; private set; } = 0f;
    public bool  IsConnected { get; private set; } = false;

    // =====================================================
    // Singleton — accès facile depuis VitalSignsUI
    // =====================================================
    public static BLEManager Instance { get; private set; }

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        InitBLE();
#else
        // En mode Editor : on simule des données pour tester l'UI
        Debug.Log("[BLE] Mode Editor — simulation activée");
        InvokeRepeating(nameof(SimulateData), 2f, 1f);
#endif
    }

    // =====================================================
    // Init BLE (Android uniquement)
    // =====================================================
    void InitBLE()
    {
        BluetoothLEHardwareInterface.Initialize(true, false,
            () =>
            {
                Debug.Log("[BLE] Initialisé — démarrage du scan...");
                ScanForDevice();
            },
            (error) =>
            {
                Debug.LogError("[BLE] Erreur init : " + error);
            }
        );
    }

    void ScanForDevice()
    {
        BluetoothLEHardwareInterface.ScanForPeripheralsWithServices(
            new string[] { SERVICE_UUID },
            (address, name) =>
            {
                Debug.Log($"[BLE] Trouvé : {name} ({address})");
                if (name.Contains(DEVICE_NAME))
                {
                    BluetoothLEHardwareInterface.StopScan();
                    ConnectToDevice(address);
                }
            },
            null
        );
    }

    void ConnectToDevice(string address)
    {
        BluetoothLEHardwareInterface.ConnectToPeripheral(address,
            (addr) =>
            {
                Debug.Log("[BLE] Connecté à " + addr);
                IsConnected = true;
            },
            null,
            (addr, serviceUUID, charUUID) =>
            {
                if (charUUID.ToUpper() == CHAR_UUID.ToUpper())
                    SubscribeToNotifications(addr);
            },
            (addr) =>
            {
                Debug.LogWarning("[BLE] Déconnecté — relance du scan...");
                IsConnected = false;
                ScanForDevice();
            }
        );
    }

    void SubscribeToNotifications(string address)
    {
        BluetoothLEHardwareInterface.SubscribeCharacteristicWithDeviceAddress(
            address, SERVICE_UUID, CHAR_UUID,
            null,
            (addr, characteristic, bytes) =>
            {
                ParseData(bytes);
            }
        );
    }

    // =====================================================
    // Lecture JSON {"hr": 72.5, "rr": 16.2}
    // =====================================================
    void ParseData(byte[] bytes)
    {
        try
        {
            string json = System.Text.Encoding.UTF8.GetString(bytes);
            VitalData data = JsonUtility.FromJson<VitalData>(json);
            HeartRate = data.hr;
            RespRate  = data.rr;
            Debug.Log($"[BLE] Reçu → HR={data.hr} bpm | RR={data.rr} rpm");
        }
        catch (Exception e)
        {
            Debug.LogError("[BLE] Erreur parsing JSON : " + e.Message);
        }
    }

    // =====================================================
    // Simulation Editor (pour tester sans Quest)
    // =====================================================
    void SimulateData()
    {
        HeartRate   = Mathf.Round(UnityEngine.Random.Range(65f, 80f) * 10f) / 10f;
        RespRate    = Mathf.Round(UnityEngine.Random.Range(14f, 20f) * 10f) / 10f;
        IsConnected = true;
    }

    void OnDestroy()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        BluetoothLEHardwareInterface.DeInitialize(() => { });
#endif
    }
}

// =====================================================
// Modèle JSON — doit correspondre exactement au Python
// =====================================================
[Serializable]
public class VitalData
{
    public float hr;
    public float rr;
}
