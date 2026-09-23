import { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
} from 'react-native';
import * as Location from 'expo-location';

export default function HomeScreen() {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [loading, setLoading] = useState(false);

  const getLocation = async () => {
    try {
      setLoading(true);

      const { status } =
        await Location.requestForegroundPermissionsAsync();

      if (status !== 'granted') {
        Alert.alert(
          'Location Permission Required',
          'Please allow location access to use this feature.'
        );
        setLoading(false);
        return;
      }

      const currentLocation =
        await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.High,
        });

      setLocation(currentLocation);
      setLoading(false);
    } catch (error) {
      console.log(error);

      Alert.alert(
        'Location Error',
        'Unable to get your current location.'
      );

      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>

      <View style={styles.header}>
        <Text style={styles.title}>
          Landslide Digital Twin
        </Text>

        <Text style={styles.subtitle}>
          Hyperlocal Landslide Early Warning System
        </Text>
      </View>

      <View style={styles.statusCard}>
        <Text style={styles.statusTitle}>
          Current Risk Status
        </Text>

        <Text style={styles.riskLevel}>
          LOW RISK
        </Text>

        <Text style={styles.riskDescription}>
          No immediate landslide threat detected at the selected location.
        </Text>
      </View>

      <TouchableOpacity
        style={styles.locationButton}
        onPress={getLocation}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Getting Location...' : '📍 Select Location'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.mapButton}>
        <Text style={styles.buttonText}>
          🗺️ View Risk Map
        </Text>
      </TouchableOpacity>

      {location && (
        <View style={styles.locationCard}>
          <Text style={styles.locationTitle}>
            Your Location
          </Text>

          <Text style={styles.locationText}>
            Latitude: {location.coords.latitude.toFixed(6)}
          </Text>

          <Text style={styles.locationText}>
            Longitude: {location.coords.longitude.toFixed(6)}
          </Text>
        </View>
      )}

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>
          Monitoring Parameters
        </Text>

        <Text style={styles.infoText}>
          🌧 Rainfall
        </Text>

        <Text style={styles.infoText}>
          ⛰ Slope & Elevation
        </Text>

        <Text style={styles.infoText}>
          🌱 Soil Wetness
        </Text>

        <Text style={styles.infoText}>
          🛰 Satellite Deformation
        </Text>
      </View>

      <Text style={styles.footer}>
        AI-Based Landslide Monitoring • North Eastern India
      </Text>

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
    padding: 20,
    paddingTop: 60,
  },

  header: {
    marginBottom: 25,
  },

  title: {
    fontSize: 27,
    fontWeight: 'bold',
    color: '#172B4D',
  },

  subtitle: {
    fontSize: 14,
    color: '#667085',
    marginTop: 6,
  },

  statusCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 22,
    marginBottom: 18,
    elevation: 3,
  },

  statusTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#344054',
  },

  riskLevel: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#16A34A',
    marginTop: 12,
  },

  riskDescription: {
    fontSize: 14,
    color: '#667085',
    marginTop: 8,
    lineHeight: 21,
  },

  locationButton: {
    backgroundColor: '#2563EB',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 12,
  },

  mapButton: {
    backgroundColor: '#172B4D',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 20,
  },

  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },

  locationCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 20,
    marginBottom: 18,
    elevation: 2,
  },

  locationTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#344054',
    marginBottom: 10,
  },

  locationText: {
    fontSize: 14,
    color: '#475467',
    marginBottom: 6,
  },

  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 20,
    elevation: 2,
  },

  infoTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#344054',
    marginBottom: 14,
  },

  infoText: {
    fontSize: 14,
    color: '#475467',
    marginBottom: 10,
  },

  footer: {
    textAlign: 'center',
    color: '#98A2B3',
    fontSize: 11,
    marginTop: 'auto',
    marginBottom: 10,
  },
});