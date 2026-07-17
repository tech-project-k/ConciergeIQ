package com.conciergeiq.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.util.UUID;

@Entity
@Table(name = "activities")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Activity {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "trip_id", nullable = false)
    @JsonIgnore
    private Trip trip;

    @Column(name = "day_number", nullable = false)
    private Integer dayNumber;

    @Column(nullable = false)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false)
    private String type; // hotel, breakfast, lunch, dinner, museum, event, attraction, transit, rest, coffee

    @Column(name = "start_time")
    private String startTime; // HH:MM

    @Column(name = "end_time")
    private String endTime; // HH:MM

    private Double latitude;
    private Double longitude;
    private String address;

    @Column(name = "contact_phone")
    private String contactPhone;

    @Column(name = "contact_website")
    private String contactWebsite;

    private Double cost = 0.0;

    @Column(name = "travel_distance_km")
    private Double travelDistanceKm;

    @Column(name = "travel_duration_min")
    private Double travelDurationMin;

    @Column(name = "travel_mode")
    private String travelMode;

    @Column(name = "booking_confirmation_code")
    private String bookingConfirmationCode;
}
