Multiple Lights 
by ΒΙΣΚΑΔΟΥΡΑΚΗΣ ΕΜΜΑΝΟΥΗΛ (csd5368@csd.uoc.gr), ΣΑΒΒΙΔΗΣ ΑΛΕΞΑΝΔΡΟΣ (csd5002@csd.uoc.gr)

Το module Multi Lights περιέχει:

mul_lights_3cubes_flat.py
mul_lights_3cubes_smooth
mul_lights_spheres.py

Τα παραδείγματα αυτά δείχνουν Phong φωτισμό με πολλαπλά φώτα, και τη διαφορά flat vs smooth normal shading σε διαφορετικά αντικείμενα.
Χρησιμοποιούν πολλαπλά φώτα (Point/Directional/Spot) και μπορούν να ελεγχθούν δυναμικά από ImGUI (π.χ. add/remove lights, αλλαγή light intensity/color/position, animation). 


Οι shaders χωρίζονται σε:

solid/per-vertex color shaders: (PHONG_MULTI_LIGHTS) και 

texture shaders: (TEXTURE_PHONG_MULTI_LIGHTS)



α) mul_lights_3cubes_flat.py: 3 κύβοι με flat normal shading, πολλαπλά lights, ImGUI control.

3 κύβοι με ίδια γεωμετρία, αλλά διαφορετικό base color:

Κύβος 1: Per-vertex colors (χρώμα ανά κορυφή)

Κύβος 2: Solid material color (ένα σταθερό material χρώμα)

Κύβος 3: Textured (albedo/texture)

Τα normals είναι flat, κάθε face έχει “σκληρό” φωτισμό χωρίς ομαλή μετάβαση μεταξύ faces.

Shaders:
Για per-vertex και solid cube: PHONG_MULTI_LIGHTS.vert/.frag

Υποστηρίζει είτε vertex-color είτε solid-color (με uniform is_solid_color και ένα materialColor). 

Για textured cube: TEXTURE_PHONG_MULTI_LIGHTS.vert/.frag



β) mul_lights_3cubes_smooth.py: 3 κύβοι με smooth normal shading, πολλαπλά lights, ImGUI control.

Ίδια σκηνή με το α): 3 κύβοι (vertex-color, solid color, textured)

Η διαφορά είναι ότι οι normals είναι smooth (averaged per shared vertex position), άρα το specular/diffuse “τρέχει” ομαλά πάνω στο object.

Σε κύβο, η χρήση smooth normals σημαίνει “πιο σφαιρική” συμπεριφορά φωτισμού (ΜΗ ΡΕΑΛΙΣΤΙΚΗ για cubes) οπότε και οι ακμές του χάνονται και το σχήμα καμπυλώνει.

Shaders: Τα ίδια με το α)




γ) mul_lights_spheres.py: 2 σφαίρες solid color, μία flat και μία smooth, πολλαπλά lights, ImGUI control.

2 σφαίρες με solid material color όπου η μία εμφανίζεται με flat shading και η άλλη με smooth shading.

Επειδή η σφαίρα θέλει smooth normals για να φαίνεται σωστά, εδώ η διαφορά γίνεται πιο εμφανής:

flat: faceted/low-poly look

smooth: σωστό continuous highlight

Shaders:

Χρησιμοποιεί τους PHONG_MULTI_LIGHTS.vert/.frag  για material-based χρώμα (με is_solid_color = 1 και ένα materialColor).
