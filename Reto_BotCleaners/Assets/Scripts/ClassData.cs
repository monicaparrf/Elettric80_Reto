using System.Collections.Generic;
using System.Numerics;

[System.Serializable]
public class WarehouseId
{
    public string warehouseId;
}

[System.Serializable]
public class RobotData
{
    public int unique_id;
    public float battery;
    public int[] position;
    public bool has_box;
}

[System.Serializable]
public class BoxData
{
    public int unique_id;
    public int carried_by_robot;
    public int[] position;
    public int weight;
}

[System.Serializable]
public class ShelveData
{
    public int unique_id;
    public int stored_box;
    public int[] position;
}

[System.Serializable]
public class ChargerData
{
    public int unique_id;
    public bool is_occupied;
    public int[] position;
}

[System.Serializable]
public class ConveyorData
{
    public int unique_id;
    public bool has_box;
    public int[] position;
}

[System.Serializable]
public class StepData
{
    public RobotData[] Robots;
    public BoxData[] Boxes;
    public ShelveData[] Shelves;
    public ChargerData[] Chargers;
    public ConveyorData[] ConveyorBelts;
}
