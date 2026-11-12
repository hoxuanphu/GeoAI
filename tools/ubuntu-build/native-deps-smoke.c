#include <gtk/gtk.h>
#include <webkit2/webkit2.h>
int main(void) {
    if (!gtk_init_check(NULL, NULL)) return 1;
    return webkit_get_major_version() < 2;
}
