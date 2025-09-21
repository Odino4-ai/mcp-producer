# 🧪 Simple Rio Test - Verify All Functions Work

## 🎯 **Quick Test Sentences (Copy-paste one by one)**

### **Test 1: Basic Documentation**
```
"We're starting a new mobile app project called DoggyDelivery."
```
**Expected:** Rio creates a section with title + mobile app image

---

### **Test 2: Image Replacement**
```
"Replace the image with a cat instead."
```
**Expected:** Rio replaces the mobile app image with a cat image

---

### **Test 3: Table Creation**
```
"Add a table with our team members at the beginning."
```
**Expected:** Rio creates a table at the top with team data

---

### **Test 4: Content Update**
```
"Actually, the app is called PetExpress now."
```
**Expected:** Rio updates the existing title (doesn't create new section)

---

### **Test 5: Complete Replacement**
```
"Replace all content with just 'FINAL DOCUMENT'."
```
**Expected:** Page becomes empty with only "FINAL DOCUMENT" as title

---

### **Test 6: Reconstruction**
```
"Document our project: PetExpress app, team of 3, budget 50k."
```
**Expected:** Rio creates a complete structured document

---

## ✅ **Verification Checklist**

After each test, verify:

- [ ] **Rio used the correct tool** (check logs)
- [ ] **Page was modified correctly** (not just described)
- [ ] **No duplicate content** (updates existing sections)
- [ ] **Images appear** when expected
- [ ] **Tables are properly formatted**
- [ ] **Final document is clean** (no metadata/timestamps)

## 🔧 **If Something Doesn't Work:**

### **Image replacement fails:**
- Check if there are images on the page to replace
- Verify Notion API permissions

### **Tables don't appear:**
- Check Notion API table format
- Verify page permissions

### **Content keeps duplicating:**
- Check if section matching logic works
- Verify updateContentInPlace vs documentLiveContent

### **Page management fails:**
- Check delete permissions in Notion
- Verify all blocks are being found and deleted

## 🎯 **Success Criteria:**

✅ **Rio should be a perfect silent listener that:**
1. Documents what people say (not what he thinks)
2. Uses the right tool for each action
3. Creates clean, professional documents
4. Updates existing content instead of duplicating
5. Handles images and tables correctly
6. Never speaks or interrupts

**If all 6 tests pass → Rio is working perfectly!** 🚀
