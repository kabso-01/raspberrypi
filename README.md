using UnityEngine;
using TMPro;  // TextMeshPro

public class VitalSignsUI : MonoBehaviour
{
    public BLEManager bleManager;   // Glisse ton objet BLEManager ici
    public TextMeshProUGUI hrText;  // Texte HR dans ta scène
    public TextMeshProUGUI rrText;  // Texte RR dans ta scène
    public TextMeshProUGUI statusText;

    void Update()
    {
        if (bleManager.IsConnected)
        {
            hrText.text     = $"{bleManager.HeartRate:F0} bpm";
            rrText.text     = $"{bleManager.RespRate:F1} resp/min";
            statusText.text = "Connecté";
            statusText.color = Color.green;
        }
        else
        {
            statusText.text  = "Recherche radar...";
            statusText.color = Color.yellow;
        }
    }
}

