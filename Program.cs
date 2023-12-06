#nullable disable

using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        var airportsData = ParseAirportsFile();
        CreateAirspaceXml(airportsData);
    }

    static (List<(string AirportName, List<(string RunwayName, string DataRunway, List<string> SIDs)> Runways)> AirportsData, List<(string AirwayName, List<string> Waypoints)> AirwaysData, List<(string IntersectionName, string Coordinates)> IntersectionsData) ParseAirportsFile()
    {
        string filePath = "navdata/Airports.txt";
        var airportsData = new List<(string AirportName, List<(string RunwayName, string DataRunway, List<string> SIDs)> Runways)>();
        var airwaysData = new List<(string AirwayName, List<string> Waypoints)>();

        using (var reader = new StreamReader(filePath))
        {
            string line;
            string currentAirport = null;
            var runways = new List<(string RunwayName, string DataRunway, List<string> SIDs)>();

            while ((line = reader.ReadLine()) != null)
            {
                var parts = line.Split(',');

                if (parts[0] == "A")
                {
                    if (currentAirport != null)
                    {
                        airportsData.Add((currentAirport, runways));
                        runways = new List<(string RunwayName, string DataRunway, List<string> SIDs)>();
                    }

                    currentAirport = parts[1];
                }
                else if (parts[0] == "R")
                {
                    string sidFilePath = $"navdata/Proc/{currentAirport}.txt";
                    var sids = new List<string>();

                    if (File.Exists(sidFilePath))
                    {
                        using (var sidReader = new StreamReader(sidFilePath))
                        {
                            string sidLine;

                            while ((sidLine = sidReader.ReadLine()) != null)
                            {
                                var sidParts = sidLine.Split(',');

                                if (sidParts[0] == "SID" && sidParts[2] == parts[1])
                                {
                                    sids.Add(sidParts[1]);
                                }
                            }
                        }
                    }

                    runways.Add((parts[1], parts[2], sids));
                }
            }

            if (currentAirport != null)
            {
                airportsData.Add((currentAirport, runways));
            }

            string airwaysFilePath = "navdata/ATS.txt";

            if (File.Exists(airwaysFilePath))
            {
                using (var airwaysReader = new StreamReader(airwaysFilePath))
                {
                    string airwaysLine;
                    string currentAirway = null;
                    var waypoints = new List<string>();

                    while ((airwaysLine = airwaysReader.ReadLine()) != null)
                    {
                        var airwaysParts = airwaysLine.Split(',');

                        if (airwaysParts[0] == "A")
                        {
                            if (currentAirway != null)
                            {
                                airwaysData.Add((currentAirway, waypoints));
                                waypoints = new List<string>();
                            }

                            currentAirway = airwaysParts[1];
                        }
                        else if (airwaysParts[0] == "S")
                        {
                            waypoints.Add(airwaysParts[1]);
                        }
                    }

                    if (currentAirway != null)
                    {
                        airwaysData.Add((currentAirway, waypoints));
                    }
                }
            }
            string waypointsFilePath = "navdata/Waypoints.txt";
            var intersectionsData = new List<(string IntersectionName, string Coordinates)>();

            if (File.Exists(waypointsFilePath))
            {
                using (var waypointsReader = new StreamReader(waypointsFilePath))
                {
                    string waypointsLine;

                    while ((waypointsLine = waypointsReader.ReadLine()) != null)
                    {
                        var waypointsParts = waypointsLine.Split(',');

                        string intersectionName = waypointsParts[0];
                        string coordinates = "+" + waypointsParts[1].Replace(".", "") + "+" + waypointsParts[2].Replace(".", "");

                        intersectionsData.Add((intersectionName, coordinates));
                    }
                }
            }

            return (airportsData, airwaysData, intersectionsData);
        }
    }

    static void CreateAirspaceXml((List<(string AirportName, List<(string RunwayName, string DataRunway, List<string> SIDs)> Runways)> AirportsData, List<(string AirwayName, List<string> Waypoints)> AirwaysData, List<(string IntersectionName, string Coordinates)> IntersectionsData) data)
    {
        XmlDocument doc = new XmlDocument();
        XmlNode root = doc.CreateElement("Airspace");
        XmlNode systemRunways = doc.CreateElement("SystemRunways");
        root.AppendChild(systemRunways);
        doc.AppendChild(root);

        foreach (var airportData in data.AirportsData)
        {
            XmlNode airportNode = doc.CreateElement("Airport");
            XmlAttribute airportNameAttr = doc.CreateAttribute("Name");
            airportNameAttr.Value = airportData.AirportName;
            airportNode.Attributes.Append(airportNameAttr);

            foreach (var runwayData in airportData.Runways)
            {
                XmlNode runwayNode = doc.CreateElement("Runway");
                XmlAttribute runwayNameAttr = doc.CreateAttribute("Name");
                runwayNameAttr.Value = runwayData.RunwayName;
                runwayNode.Attributes.Append(runwayNameAttr);

                XmlAttribute dataRunwayAttr = doc.CreateAttribute("DataRunway");
                dataRunwayAttr.Value = runwayData.DataRunway;
                runwayNode.Attributes.Append(dataRunwayAttr);

                foreach (var sid in runwayData.SIDs)
                {
                    XmlNode sidNode = doc.CreateElement("SID");
                    XmlAttribute sidNameAttr = doc.CreateAttribute("Name");
                    sidNameAttr.Value = sid;
                    sidNode.Attributes.Append(sidNameAttr);

                    runwayNode.AppendChild(sidNode);
                }

                airportNode.AppendChild(runwayNode);
            }

            systemRunways.AppendChild(airportNode);
        }

        XmlNode airwaysNode = doc.CreateElement("Airways");
        root.AppendChild(airwaysNode);

        foreach (var airwayData in data.AirwaysData)
        {
            XmlNode airwayNode = doc.CreateElement("Airway");
            XmlAttribute airwayNameAttr = doc.CreateAttribute("Name");
            airwayNameAttr.Value = airwayData.AirwayName;
            airwayNode.Attributes.Append(airwayNameAttr);

            foreach (var waypoint in airwayData.Waypoints)
            {
                XmlNode waypointNode = doc.CreateTextNode(waypoint + "/");
                airwayNode.AppendChild(waypointNode);
            }

            airwaysNode.AppendChild(airwayNode);
        }

        XmlNode intersectionsNode = doc.CreateElement("Intersections");
        root.AppendChild(intersectionsNode);

        foreach (var intersectionData in data.IntersectionsData)
        {
            XmlNode intersectionNode = doc.CreateElement("Point");
            XmlAttribute intersectionNameAttr = doc.CreateAttribute("Name");
            intersectionNameAttr.Value = intersectionData.IntersectionName;
            intersectionNode.Attributes.Append(intersectionNameAttr);

            XmlAttribute typeAttr = doc.CreateAttribute("Type");
            typeAttr.Value = "Fix";
            intersectionNode.Attributes.Append(typeAttr);

            intersectionNode.InnerText = intersectionData.Coordinates;

            intersectionsNode.AppendChild(intersectionNode);
        }

        XmlNode navaidsNode = doc.CreateElement("Navaids");
        root.AppendChild(navaidsNode);

        string[] lines = System.IO.File.ReadAllLines("navdata/Navaids.txt");

        foreach (string line in lines)
        {
            string[] attributes = line.Split(',');

            XmlNode navaidNode = doc.CreateElement("Point");
            XmlAttribute nameAttr = doc.CreateAttribute("Name");
            nameAttr.Value = attributes[0];
            navaidNode.Attributes.Append(nameAttr);

            XmlAttribute typeAttr = doc.CreateAttribute("Type");
            typeAttr.Value = "Navaid";
            navaidNode.Attributes.Append(typeAttr);

            XmlAttribute navaidTypeAttr = doc.CreateAttribute("NavaidType");
            navaidTypeAttr.Value = "NDB";
            navaidNode.Attributes.Append(navaidTypeAttr);

            XmlAttribute frequencyAttr = doc.CreateAttribute("Frequency");
            frequencyAttr.Value = attributes[2];
            navaidNode.Attributes.Append(frequencyAttr);

            navaidNode.InnerText = $"{attributes[6]}{attributes[7]}";

            navaidsNode.AppendChild(navaidNode);
        }

        XmlNode sidstarsNode = doc.CreateElement("SIDSTARs");
        root.AppendChild(sidstarsNode);

        foreach (string file in Directory.EnumerateFiles("navdata/Proc", "*.txt"))
        {
            string[] fileLines = System.IO.File.ReadAllLines(file);
            List<string> route = new List<string>();
            string currentSidStar = null;

            foreach (string line in fileLines)
            {
                string[] attributes = line.Split(',');

                if (attributes[0] == "SID" || attributes[0] == "STAR")
                {
                    if (route.Count > 0)
                    {
                        XmlNode previousRouteNode = sidstarsNode.LastChild;
                        XmlNode previousRunwayNode = previousRouteNode.LastChild;
                        previousRunwayNode.InnerText = string.Join("/", route);
                        route.Clear();
                    }

                    if (currentSidStar != attributes[1])
                    {
                        currentSidStar = attributes[1];

                        XmlNode routeNode = doc.CreateElement(attributes[0]);
                        XmlAttribute nameAttr = doc.CreateAttribute("Name");
                        nameAttr.Value = attributes[1];
                        routeNode.Attributes.Append(nameAttr);

                        XmlAttribute airportAttr = doc.CreateAttribute("Airport");
                        airportAttr.Value = Path.GetFileNameWithoutExtension(file);
                        routeNode.Attributes.Append(airportAttr);

                        sidstarsNode.AppendChild(routeNode);
                    }

                    if (attributes[2].All(char.IsDigit))
                    {
                        XmlAttribute runwaysAttr = doc.CreateAttribute("Runways");
                        runwaysAttr.Value = attributes[2];
                        sidstarsNode.LastChild.Attributes.Append(runwaysAttr);

                        XmlNode runwayNode = doc.CreateElement("Route");
                        XmlAttribute runwayAttr = doc.CreateAttribute("Runway");
                        runwayAttr.Value = attributes[2];
                        runwayNode.Attributes.Append(runwayAttr);
                        sidstarsNode.LastChild.AppendChild(runwayNode);
                    }
                    else
                    {
                        XmlNode transitionNode = doc.CreateElement("Transition");
                        XmlAttribute transitionAttr = doc.CreateAttribute("Name");
                        transitionAttr.Value = attributes[2];
                        transitionNode.Attributes.Append(transitionAttr);
                        sidstarsNode.LastChild.AppendChild(transitionNode);
                    }
                }
                else if (attributes[0] == "TF" || attributes[0] == "CF" || attributes[0] == "IF")
                {
                    route.Add(attributes[1]);
                }
            }

            if (route.Count > 0)
            {
                XmlNode lastRouteNode = sidstarsNode.LastChild;
                XmlNode lastRunwayNode = lastRouteNode.LastChild;
                lastRunwayNode.InnerText = string.Join("/", route);
            }
        }

        XmlNode approachesNode = doc.CreateElement("Approaches");
        root.AppendChild(approachesNode);

        foreach (string file in Directory.EnumerateFiles("navdata/Proc", "*.txt"))
        {
            string[] fileLines = System.IO.File.ReadAllLines(file);
            List<string> route = new List<string>();
            string currentApproach = null;

            foreach (string line in fileLines)
            {
                string[] attributes = line.Split(',');

                if (attributes[0] == "APPTR" || attributes[0] == "FINAL")
                {
                    if (route.Count > 0 && approachesNode.HasChildNodes)
                    {
                        // Add the route to the previous approach
                        XmlNode previousRouteNode = approachesNode.LastChild;
                        XmlNode previousRunwayNode = previousRouteNode.LastChild;
                        previousRunwayNode.InnerText = string.Join("/", route);
                        route.Clear();
                    }

                    if (currentApproach != attributes[1])
                    {
                        // New approach
                        currentApproach = attributes[1];

                        XmlNode approachNode = doc.CreateElement("Approach");
                        XmlAttribute nameAttr = doc.CreateAttribute("Name");
                        nameAttr.Value = attributes[1];
                        approachNode.Attributes.Append(nameAttr);

                        XmlAttribute airportAttr = doc.CreateAttribute("Airport");
                        airportAttr.Value = Path.GetFileNameWithoutExtension(file);
                        approachNode.Attributes.Append(airportAttr);

                        approachesNode.AppendChild(approachNode);
                    }

                    XmlNode runwayNode = doc.CreateElement("Route");
                    XmlAttribute runwayAttr = doc.CreateAttribute("Runway");
                    runwayAttr.Value = attributes[2];
                    runwayNode.Attributes.Append(runwayAttr);
                    approachesNode.LastChild.AppendChild(runwayNode);
                }
                else if (attributes[0] == "TF" || attributes[0] == "CF" || attributes[0] == "IF" || attributes[0] == "DF")
                {
                    // Add the waypoint to the route
                    route.Add(attributes[1]);
                }
            }

            if (route.Count > 0 && approachesNode.HasChildNodes)
            {
                // Add the route to the last approach
                XmlNode lastRouteNode = approachesNode.LastChild;
                XmlNode lastRunwayNode = lastRouteNode.LastChild;
                lastRunwayNode.InnerText = string.Join("/", route);
            }
        }

        doc.Save("Airspace.xml");
    }
}

