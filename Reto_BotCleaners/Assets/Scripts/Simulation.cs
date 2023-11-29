using UnityEngine;
using UnityEngine.Networking;
using SimpleJSON;
using System.Collections;
using System.Collections.Generic;

public class Simulation : MonoBehaviour
{
    public GameObject robotPrefab;
    public GameObject boxPrefab;
    public GameObject shelvePrefab;
    public GameObject chargerPrefab;
    public GameObject conveyorPrefab;
    private List<StepData> simulationDataList = new ();

    // Start is called before the first frame update
    void Start()
    {
        StartCoroutine(StartSimulation());
    }

    // Update is called once per frame
    void Update()
    {
        if (simulationDataList.Count == 0)
        {
            return;
        }

        StepData stepData = simulationDataList[0];
        simulationDataList.RemoveAt(0);

        foreach (RobotData robot in stepData.Robots)
        {
            int uniqueId = robot.unique_id;
            float x = robot.position[0];
            float y = robot.position[1];
            Vector3 robotPosition = new Vector3((x * 10) - 0.5f, 0, y * 10);
            GameObject go = GameObject.Find("robot" + uniqueId.ToString());
            go.transform.position = robotPosition;

            // Hide box if robot is not carrying one
            if (!robot.has_box)
            {
                go.transform.GetChild(0).gameObject.SetActive(false);
            }
            else
            {
                go.transform.GetChild(0).gameObject.SetActive(true);
            }
        }

        foreach (ShelveData shelf in stepData.Shelves)
        {
            // Check if shelf has a box stored and if it has one then show it
            if (shelf.stored_box > 0)
            {
                int uniqueId = shelf.unique_id;
                GameObject go = GameObject.Find("shelf" + uniqueId.ToString());
                go.transform.GetChild(0).gameObject.SetActive(true);
            }
        }
        // Wait
        System.Threading.Thread.Sleep(500);
    }

    string fixJson(string value)
    {
        value = "{\"Items\":" + value + "}";
        return value;
    }

    IEnumerator StartSimulation()
    {
        // Post to http://127.0.0.1:5024/warehouseSimulations and generate new warehouse id
        UnityWebRequest warehouseCreationRequest = UnityWebRequest.Post("http://127.0.0.1:5024/warehouseSimulations", "");

        yield return warehouseCreationRequest.SendWebRequest();

        if (warehouseCreationRequest.error != null)
        {
            Debug.Log(warehouseCreationRequest.error);
            yield break;
        }

        var warehouseId = JsonUtility.FromJson<WarehouseId>(warehouseCreationRequest.downloadHandler.text).warehouseId;

        // Get to http://127.0.0.1:5024/warehouseSimulations/{warehouseId}?steps=10 and get the data for each step on the simulation
        UnityWebRequest warehouseSimulationRequest = UnityWebRequest.Get($"http://127.0.0.1:5024/warehouseSimulations/{warehouseId}?steps=200");

        yield return warehouseSimulationRequest.SendWebRequest();

        if (warehouseSimulationRequest.error != null)
        {
            Debug.Log(warehouseSimulationRequest.error);
            yield break;
        }

        string jsonString = fixJson(warehouseSimulationRequest.downloadHandler.text);
        var simulationData = JsonHelper.FromJson<StepData>(jsonString);

        if (simulationData == null)
        {
            Debug.Log("Nothing to see here");
            yield break;
        }

        foreach (ShelveData shelve in simulationData[0].Shelves)
        {
            int uniqueId = shelve.unique_id;
            float x = shelve.position[0];
            float y = shelve.position[1];
            Vector3 shelvePosition = new Vector3((x * 10) - 5, 9, y * 10);
            var go = Instantiate(shelvePrefab, shelvePosition, Quaternion.Euler(0, 0, -90));
            go.name = "shelf" + uniqueId.ToString();
            go.transform.GetChild(0).gameObject.SetActive(false);
        }

        foreach (ChargerData charger in simulationData[0].Chargers)
        {
            int uniqueId = charger.unique_id;
            float x = charger.position[0];
            float y = charger.position[1];
            Vector3 chargerPosition = new Vector3(x * 10, 0, y * 10);
            var go = Instantiate(chargerPrefab, chargerPosition, Quaternion.Euler(0, 0, 0));
            go.name = "charger" + uniqueId.ToString();
        }

        foreach (ConveyorData conveyor in simulationData[0].ConveyorBelts)
        {
            int uniqueId = conveyor.unique_id;
            float x = conveyor.position[0];
            float y = conveyor.position[1];
            Vector3 conveyorPosition = new Vector3(x * 10, 3, (y * 10) + 5);
            var go = Instantiate(conveyorPrefab, conveyorPosition, Quaternion.Euler(0, -90, 0));
            go.name = "belt" + uniqueId.ToString();
        }

        foreach (BoxData box in simulationData[0].Boxes)
        {
            int uniqueId = box.unique_id;
            float x = box.position[0];
            float y = box.position[1];
            Vector3 boxPosition = new Vector3(x * 10, 0, y * 10);
            var go = Instantiate(boxPrefab, boxPosition, Quaternion.Euler(0, 0, 0));
            go.name = "box" + uniqueId.ToString();
        }

        foreach (RobotData robot in simulationData[0].Robots)
        {
            int uniqueId = robot.unique_id;
            float x = robot.position[0];
            float y = robot.position[1];
            Vector3 robotPosition = new Vector3(x * 10, 0, y * 10);
            var go = Instantiate(robotPrefab, robotPosition, Quaternion.Euler(0, 0, 0));
            go.name = "robot" + uniqueId.ToString();
            go.transform.GetChild(0).gameObject.SetActive(false);
        }

        // Remove first step from simulation data
        simulationDataList = new List<StepData>(simulationData);
        simulationDataList.RemoveAt(0);
    }

    public static class JsonHelper
    {
        public static T[] FromJson<T>(string json)
        {
            Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(json);
            return wrapper.Items;
        }

        [System.Serializable]
        private class Wrapper<T>
        {
            public T[] Items;
        }
    }
}
