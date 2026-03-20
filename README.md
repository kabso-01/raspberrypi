using UnityEngine;
using System;

public class BLEManager : MonoBehaviour
{
    // Mêmes UUIDs que dans ble_server.py !
    const string SERVICE_UUID = "12345678-1234-1234-1234-123456789abc";
    const string CHAR_UUID    = "12345678-1234-1234-1234-123456789def";
    const string DEVICE_NAME  = "HrrmonieRadar";

    public float HeartRate { get; private set; }
    public float RespRate  { get; private set; }
    public bool  IsConnected { get; private set; }

    void Start()
    {
        BluetoothLEHardwareInterface.Initialize(true, false,
            () => { Debug.Log("BLE prêt"); ScanForDevice(); },
            (err) => Debug.LogError("Erreur BLE : " + err)
        );
    }

    void ScanForDevice()
    {
        BluetoothLEHardwareInterface.ScanForPeripheralsWithServices(
            new string[]{ SERVICE_UUID },
            (addr, name) => {
                if (name == DEVICE_NAME) {
                    BluetoothLEHardwareInterface.StopScan();
                    ConnectToDevice(addr);
                }
            }, null
        );
    }

    void ConnectToDevice(string address)
    {
        BluetoothLEHardwareInterface.ConnectToPeripheral(address,
            (addr) => { Debug.Log("Connecté à " + addr); IsConnected = true; },
            null,
            (addr, svc, chr) => {
                if (chr == CHAR_UUID)
                    SubscribeToNotifications(addr);
            }, null
        );
    }

    void SubscribeToNotifications(string address)
    {
        BluetoothLEHardwareInterface.SubscribeCharacteristicWithDeviceAddress(
            address, SERVICE_UUID, CHAR_UUID, null,
            (addr, chr, bytes) => ParseData(bytes)
        );
    }

    void ParseData(byte[] bytes)
    {
        string json = System.Text.Encoding.UTF8.GetString(bytes);
        VitalData data = JsonUtility.FromJson<VitalData>(json);
        HeartRate = data.hr;
        RespRate  = data.rr;
        Debug.Log($"HR={data.hr} RR={data.rr}");
    }

    void OnDestroy()
    {
        BluetoothLEHardwareInterface.DeInitialize(() => {});
    }
}

[Serializable]
public class VitalData { public float hr; public float rr; }

