<uses-feature android:name="android.hardware.bluetooth_le" android:required="true"/>

using UnityEngine;
using TMPro;

public class VitalSignsUI : MonoBehaviour
{
    // =====================================================
    // Glisse tes TextMeshPro depuis la scène Unity
    // dans ces 3 champs dans l'Inspector
    // =====================================================
    [Header("Références UI — à assigner dans l'Inspector")]
    [SerializeField] private TextMeshProUGUI hrText;
    [SerializeField] private TextMeshProUGUI rrText;
    [SerializeField] private TextMeshProUGUI statusText;

    void Update()
    {
        // Vérification de sécurité : si BLEManager n'existe pas encore
        if (BLEManager.Instance == null)
        {
            if (statusText != null)
                statusText.text = "En attente du BLEManager...";
            return;
        }

        if (BLEManager.Instance.IsConnected)
        {
            if (hrText != null)
                hrText.text = $"{BLEManager.Instance.HeartRate:F0} bpm";

            if (rrText != null)
                rrText.text = $"{BLEManager.Instance.RespRate:F1} resp/min";

            if (statusText != null)
            {
                statusText.text  = "Connecté";
                statusText.color = Color.green;
            }
        }
        else
        {
            if (hrText != null)
                hrText.text = "-- bpm";

            if (rrText != null)
                rrText.text = "-- resp/min";

            if (statusText != null)
            {
                statusText.text  = "Recherche radar...";
                statusText.color = Color.yellow;
            }
        }
    }

    // =====================================================
    // Vérifie que les références sont bien assignées
    // =====================================================
    void OnValidate()
    {
        if (hrText == null)
            Debug.LogWarning("[VitalSignsUI] hrText non assigné dans l'Inspector !");
        if (rrText == null)
            Debug.LogWarning("[VitalSignsUI] rrText non assigné dans l'Inspector !");
        if (statusText == null)
            Debug.LogWarning("[VitalSignsUI] statusText non assigné dans l'Inspector !");
    }
}
